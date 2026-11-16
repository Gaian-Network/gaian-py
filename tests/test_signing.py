import json
import re
import time
from pathlib import Path

import httpx
import pytest

from .conftest import API_KEY, SECRET
from .gateway_fake import gateway_verify

VECTORS = json.loads((Path(__file__).parent / "data" / "signature-vectors.json").read_text("utf-8"))
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


@pytest.mark.parametrize("vector", VECTORS["requests"], ids=lambda v: v["name"])
def test_sign_vectors(vector):
    from gaian._core import sign_request

    got = sign_request(
        api_key=VECTORS["apiKey"],
        secret_key=VECTORS["secretKey"],
        method=vector["method"],
        path=vector["path"],
        query=vector["query"],
        body=vector["body"],
        timestamp=VECTORS["timestamp"],
    )

    assert got == vector["signature"]


@pytest.fixture
def fake_gateway(httpx_mock):
    checks = []

    def respond(request: httpx.Request) -> httpx.Response:
        checks.append((request, gateway_verify(request, API_KEY, SECRET)))
        return httpx.Response(200, json={"requestId": "r1", "data": None})

    httpx_mock.add_callback(respond, is_reusable=True)
    return checks


async def test_get_with_query_signs_empty_body_and_sends_none(gw, fake_gateway):
    await gw.call("list_user_orders", user_id="usr_1", status="completed", page=2, page_size=50)

    request, check = fake_gateway[0]
    assert check.signed_body == ""
    assert check.ok
    assert request.content == b""
    assert request.url.params["status"] == "completed"


async def test_get_query_is_signed_exactly_as_sent(gw, fake_gateway):
    await gw.call("list_user_orders", user_id="usr_1", status="in progress&x=ü")

    request, check = fake_gateway[0]
    assert request.url.params["status"] == "in progress&x=ü"
    assert check.ok


async def test_get_list_banks_signature_matches(gw, fake_gateway):
    await gw.call("list_banks", country="VN")

    assert fake_gateway[0][1].ok


async def test_post_body_with_html_chars_and_vietnamese_text_signs_like_gateway(gw, fake_gateway):
    await gw.call(
        "quote",
        qr_string="Nguyễn & <Co>",
        amount=150000,
        chain_id=101,
        settlement_currency="USDC",
        user_id="usr_1",
    )

    _, check = fake_gateway[0]
    assert "\\u0026" in check.signed_body
    assert check.ok


async def test_post_without_body_signs_empty_body(gw, fake_gateway):
    await gw.call("create_user")

    _, check = fake_gateway[0]
    assert check.signed_body == ""
    assert check.ok


async def test_post_whose_fields_are_all_empty_signs_empty_body(gw, fake_gateway):
    await gw.call("update_kyc", user_id="usr_1")

    _, check = fake_gateway[0]
    assert check.signed_body == ""
    assert check.ok


@pytest.mark.parametrize(
    "wallet, signed_path",
    [
        ("eip155:1:0xAbC", "/api/v2/users/wallet/eip15510xAbC"),
        ("addr with space", "/api/v2/users/wallet/addr with space"),
        ("a/b", "/api/v2/users/wallet/a/b"),
    ],
    ids=["colon", "space", "slash"],
)
async def test_path_is_signed_decoded_without_colons(gw, fake_gateway, wallet, signed_path):
    await gw.call("get_user_by_wallet", wallet_address=wallet)

    _, check = fake_gateway[0]
    assert check.signed_path == signed_path
    assert check.ok


async def test_each_request_has_uuid_request_id_and_fresh_timestamp(gw, fake_gateway):
    await gw.call("create_user")
    await gw.call("create_user")

    first, second = fake_gateway[0][1], fake_gateway[1][1]
    assert UUID.match(first.request_id)
    assert UUID.match(second.request_id)
    assert first.request_id != second.request_id
    assert abs(int(first.timestamp) - time.time()) < 10
