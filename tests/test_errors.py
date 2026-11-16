import json

import pytest

import gaian


async def failing(httpx_mock, gw, status, *, text="", headers=None):
    httpx_mock.add_response(status_code=status, content=text.encode(), headers=headers or {})
    with pytest.raises(gaian.GaianAPIError) as info:
        await gw.call("create_user")
    return info.value


async def test_flat_message_body_keeps_status_message_raw_body_and_header_request_id(
    httpx_mock, gw
):
    text = json.dumps({"message": "user not found"})

    err = await failing(httpx_mock, gw, 404, text=text, headers={"X-Request-ID": "req-hdr-1"})

    assert err.status_code == 404
    assert err.code == "NOT_FOUND"
    assert err.message == "user not found"
    assert err.request_id == "req-hdr-1"
    assert err.body == text


async def test_payments_body_exposes_service_code_and_body_request_id(httpx_mock, gw):
    text = json.dumps(
        {
            "success": False,
            "requestId": "req-pay-1",
            "error": {
                "code": "IDENTITY_REQUIRED",
                "message": "identity required",
                "details": {"field": "userId"},
            },
        }
    )

    err = await failing(httpx_mock, gw, 400, text=text)

    assert err.status_code == 400
    assert err.code == "BAD_REQUEST"
    assert err.api_code == "IDENTITY_REQUIRED"
    assert err.message == "identity required"
    assert err.request_id == "req-pay-1"
    assert err.body == text


@pytest.mark.parametrize(
    "status, code",
    [
        (400, "BAD_REQUEST"),
        (401, "UNAUTHORIZED"),
        (403, "FORBIDDEN"),
        (404, "NOT_FOUND"),
        (409, "CONFLICT"),
        (500, "SERVER_ERROR"),
        (502, "SERVER_ERROR"),
    ],
)
async def test_http_status_maps_to_code(httpx_mock, gw, status, code):
    err = await failing(httpx_mock, gw, status, text=json.dumps({"message": "x"}))

    assert err.code == code


async def test_402_422_and_429_get_their_own_codes(httpx_mock, gw):
    codes = []
    for status in (402, 422, 429):
        err = await failing(httpx_mock, gw, status, text=json.dumps({"message": "x"}))
        assert err.status_code == status
        codes.append(err.code)

    assert len(set(codes)) == 3
    assert not {"UNKNOWN", "SERVER_ERROR"} & set(codes)


async def test_502_with_empty_body_is_a_server_error_with_usable_message(httpx_mock, gw):
    err = await failing(httpx_mock, gw, 502)

    assert err.code == "SERVER_ERROR"
    assert err.status_code == 502
    assert "502" in err.message
    assert err.body == ""


async def test_503_with_html_body_keeps_raw_html(httpx_mock, gw):
    html = "<html><body>Service Unavailable</body></html>"

    err = await failing(httpx_mock, gw, 503, text=html)

    assert err.code == "SERVER_ERROR"
    assert err.body == html


async def test_is_not_found_sees_through_a_wrapping_exception(httpx_mock, gw):
    err = await failing(httpx_mock, gw, 404, text=json.dumps({"message": "gone"}))

    try:
        raise RuntimeError("loading user failed") from err
    except RuntimeError as wrapped:
        assert gaian.is_not_found(wrapped)
        assert not gaian.is_conflict(wrapped)
    assert gaian.is_not_found(err)
