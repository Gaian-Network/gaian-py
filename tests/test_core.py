import inspect
import logging

import httpx
import pytest

import gaian
from gaian._core import canonical_body, canonical_json, encode_query

from .conftest import API_KEY, SECRET, sent


@pytest.mark.parametrize(
    "value, text",
    [
        (150000, "150000"),
        (150000.0, "150000"),
        (-0.0, "-0"),
        (0.00001, "0.00001"),
        (0.0000015, "0.0000015"),
        (1.5e-7, "1.5e-7"),
        (1e-10, "1e-10"),
        (1.2345678901234568e20, "123456789012345680000"),
        (1.5e22, "1.5e+22"),
        (10**21, "1e+21"),
        (gaian.Chain.SOLANA, "101"),
        (gaian.DocumentType.PASSPORT, '"PASSPORT"'),
        (True, "true"),
        ("a b", '"a\\u2028b"'),
        (("x", 1), '["x",1]'),
    ],
)
def test_canonical_json_writes_values_like_the_gateway(value, text):
    assert canonical_json(value) == text


@pytest.mark.parametrize("value", [float("nan"), float("inf"), {1: "a"}, b"raw", object()])
def test_canonical_json_rejects_values_json_cannot_carry(value):
    with pytest.raises((TypeError, ValueError)):
        canonical_json(value)


def test_canonical_body_is_empty_for_none_and_empty_object_only():
    assert canonical_body(None) == ""
    assert canonical_body({}) == ""
    assert canonical_body({"a": 0, "b": False}) == '{"a":0,"b":false}'


def test_encode_query_sorts_keys_and_skips_none_and_empty_but_keeps_zero_and_false():
    query = encode_query({"z": 0, "b": None, "a": "x y", "c": "", "d": False})

    assert query == "a=x+y&d=false&z=0"


@pytest.mark.parametrize("missing", ["api_key", "secret_key"])
@pytest.mark.parametrize("cls", [gaian.GaianClient, gaian.AsyncGaianClient])
def test_client_requires_both_keys(cls, missing):
    keys = {"api_key": API_KEY, "secret_key": SECRET, missing: ""}

    with pytest.raises(ValueError, match=missing):
        cls(**keys)


async def test_empty_path_parameter_raises_before_any_request(httpx_mock, gw):
    with pytest.raises(ValueError, match="user_id is required"):
        await gw.call("get_user_by_id", user_id="")

    assert httpx_mock.get_requests() == []


async def test_request_carries_auth_headers_and_versioned_user_agent(httpx_mock, gw):
    httpx_mock.add_response(json={"requestId": "r1", "data": {"userId": "usr_1"}})

    await gw.call("create_user")

    headers = sent(httpx_mock).headers
    assert headers["x-gaian-key"] == API_KEY
    assert headers["x-gaian-signature"]
    assert headers["user-agent"] == f"gaian-python-sdk/{gaian.VERSION}"
    assert gaian.VERSION == gaian.__version__ == "2.0.0"


async def test_timeout_is_a_timeout_error_that_keeps_the_httpx_cause(httpx_mock, gw):
    httpx_mock.add_exception(httpx.ReadTimeout("slow"))

    with pytest.raises(gaian.GaianTimeoutError) as info:
        await gw.call("place_order", quote_id="q1")

    assert isinstance(info.value.__cause__, httpx.ReadTimeout)
    assert "POST /api/v2/orders" in str(info.value)


async def test_network_failure_is_a_connection_error_but_not_a_timeout(httpx_mock, gw):
    httpx_mock.add_exception(httpx.ConnectError("refused"))

    with pytest.raises(gaian.GaianConnectionError) as info:
        await gw.call("create_user")

    assert not isinstance(info.value, gaian.GaianTimeoutError)
    assert isinstance(info.value, gaian.GaianError)


@pytest.mark.parametrize(
    "content",
    [b"", b"<html>ok</html>", b"[1,2]", b'{"requestId":"r1","data":{"userId":{"secret-value":1}}}'],
    ids=["empty", "html", "not_an_object", "wrong_type"],
)
async def test_undecodable_2xx_body_raises_invalid_response_without_quoting_values(
    httpx_mock, gw, content
):
    httpx_mock.add_response(content=content, headers={"X-Request-ID": "req-9"})

    with pytest.raises(gaian.GaianInvalidResponseError) as info:
        await gw.call("create_user")

    assert info.value.status_code == 200
    assert info.value.request_id == "req-9"
    assert info.value.body == content.decode()
    assert "secret-value" not in str(info.value)
    assert info.value.__cause__ is None and info.value.__context__ is None


async def test_missing_and_null_response_fields_take_defaults_and_unknown_ones_are_ignored(
    httpx_mock, gw
):
    httpx_mock.add_response(
        json={"success": True, "requestId": None, "data": {"orderId": None, "newField": 1}}
    )

    resp = await gw.call("get_order_status", order_id="ord_1")

    assert resp.request_id == ""
    assert (resp.data.order_id, resp.data.status, resp.data.fiat_amount) == ("", 0, 0)
    assert resp.data.chain_id is None


async def test_unknown_status_values_still_decode(httpx_mock, gw):
    httpx_mock.add_response(
        json={"requestId": "r1", "data": {"markets": {"VN": {"status": "NEW"}}}}
    )

    resp = await gw.call("get_markets", user_id="usr_1")

    assert resp.data.markets["VN"].status == "NEW"


async def test_without_debug_nothing_is_logged_by_the_sdk(httpx_mock, gw, caplog):
    httpx_mock.add_response(json={"requestId": "r1", "data": {"userId": "usr_1"}})
    caplog.set_level(logging.DEBUG)

    await gw.call("create_user")

    assert [r for r in caplog.records if r.name == "gaian"] == []


async def test_debug_goes_to_the_given_logger_with_status(httpx_mock, make_harness, caplog):
    httpx_mock.add_response(status_code=404, json={"message": "gone"})
    gw = make_harness(debug=True, logger=logging.getLogger("my.app"))
    caplog.set_level(logging.DEBUG)

    with pytest.raises(gaian.GaianAPIError):
        await gw.call("get_user_by_id", user_id="usr_1")

    messages = [r.getMessage() for r in caplog.records if r.name == "my.app"]
    assert messages == [
        "gaian request GET /api/v2/users/usr_1",
        "gaian response GET /api/v2/users/usr_1 status=404",
    ]


async def test_api_error_text_names_status_codes_message_and_request_id(httpx_mock, gw):
    httpx_mock.add_response(
        status_code=429,
        json={"success": False, "requestId": "req-7", "error": {"code": "SLOW", "message": "wait"}},
    )

    with pytest.raises(gaian.GaianAPIError) as info:
        await gw.call("create_user")

    assert str(info.value) == (
        "gaian: api error: status=429 code=RATE_LIMITED api_code=SLOW message=wait request_id=req-7"
    )
    assert gaian.is_rate_limited(info.value)
    assert not gaian.is_unauthorized(info.value) and not gaian.is_forbidden(info.value)


def test_caller_supplied_http_client_is_used_and_left_open():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"requestId": "r1", "data": {"userId": "usr_1"}})

    http = httpx.Client(transport=httpx.MockTransport(handler))
    with gaian.GaianClient(api_key=API_KEY, secret_key=SECRET, http_client=http) as client:
        assert client.create_user().data.user_id == "usr_1"

    assert seen[0].url.host == "sandbox.gaian.network"
    assert not http.is_closed
    http.close()


def test_base_url_trailing_slash_is_dropped():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://gw.test/api/v2/users"
        return httpx.Response(200, json={"requestId": "r1", "data": None})

    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = gaian.GaianClient(
        api_key=API_KEY, secret_key=SECRET, base_url="https://gw.test/", http_client=http
    )

    assert client.create_user().data is None


@pytest.mark.parametrize("cls", [gaian.GaianClient, gaian.AsyncGaianClient])
def test_client_methods_keep_the_endpoint_signature_and_doc(cls):
    params = inspect.signature(cls.quote).parameters

    assert list(params)[:3] == ["self", "qr_string", "amount"]
    assert params["user_id"].kind is inspect.Parameter.KEYWORD_ONLY
    assert cls.quote.__name__ == "quote"
    assert "single-use quote" in cls.quote.__doc__


def test_is_terminal_is_true_only_for_final_order_statuses():
    final = {s for s in gaian.OrderStatus if gaian.is_terminal(s)}

    assert final == {
        gaian.OrderStatus.COMPLETED,
        gaian.OrderStatus.FAILED,
        gaian.OrderStatus.CANCELLED,
        gaian.OrderStatus.EXPIRED,
    }
    assert not gaian.is_terminal(7)


def test_verify_webhook_rejects_an_empty_secret():
    with pytest.raises(gaian.WebhookVerificationError):
        gaian.verify_webhook(secret="", signature="sha256=00", timestamp="1", body=b"")
