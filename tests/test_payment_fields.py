import pytest

import gaian

from .conftest import body_of, sent
from .samples import PLACE_ORDER, QR_INFO, QUOTE, USER

QUOTE_KW = {"qr_string": "qr", "amount": 500000, "chain_id": 101, "settlement_currency": "USDC"}
QUOTE_BODY = {"qrString": "qr", "amount": 500000, "chainId": 101, "settlementCurrency": "USDC"}


async def test_quote_sends_wallet_address_network_and_from_address_instead_of_user_id(
    httpx_mock, gw
):
    httpx_mock.add_response(json={"success": True, "requestId": "r1", "data": QUOTE})

    await gw.call(
        "quote", **QUOTE_KW, network="YAPE", from_address="0xfrom", wallet_address="0xabc"
    )

    assert body_of(sent(httpx_mock)) == {
        **QUOTE_BODY,
        "network": "YAPE",
        "fromAddress": "0xfrom",
        "walletAddress": "0xabc",
    }


async def test_quote_sends_email_instead_of_user_id(httpx_mock, gw):
    httpx_mock.add_response(json={"success": True, "requestId": "r1", "data": QUOTE})

    await gw.call("quote", **QUOTE_KW, email="a@example.com")

    assert body_of(sent(httpx_mock)) == {**QUOTE_BODY, "email": "a@example.com"}


async def test_quote_without_identity_is_not_blocked_and_returns_server_400(httpx_mock, gw):
    httpx_mock.add_response(
        status_code=400,
        json={
            "success": False,
            "requestId": "r1",
            "error": {"code": "IDENTITY_REQUIRED", "message": "identity required"},
        },
    )

    with pytest.raises(gaian.GaianAPIError) as info:
        await gw.call("quote", **QUOTE_KW)

    assert len(httpx_mock.get_requests()) == 1
    assert info.value.status_code == 400
    assert info.value.api_code == "IDENTITY_REQUIRED"


async def test_quote_prefund_sends_email_identity(httpx_mock, gw):
    httpx_mock.add_response(json={"success": True, "requestId": "r1", "data": QUOTE})

    await gw.call(
        "quote_prefund", qr_string="qr", amount=1, settlement_currency="USDC", email="a@example.com"
    )

    assert body_of(sent(httpx_mock)) == {
        "qrString": "qr",
        "amount": 1,
        "settlementCurrency": "USDC",
        "email": "a@example.com",
    }


async def test_parse_qr_sends_network_and_all_identities(httpx_mock, gw):
    httpx_mock.add_response(
        json={"success": True, "requestId": "r1", "data": {**QR_INFO, "bankName": "Yape"}}
    )

    resp = await gw.call(
        "parse_qr",
        qr_string="qr",
        country="PE",
        network="PLIN",
        user_id="u1",
        email="a@example.com",
        wallet_address="0xabc",
    )

    assert body_of(sent(httpx_mock)) == {
        "qrString": "qr",
        "country": "PE",
        "network": "PLIN",
        "userId": "u1",
        "email": "a@example.com",
        "walletAddress": "0xabc",
    }
    assert resp.data.bank_name == "Yape"


async def test_quote_response_has_settlement_base_and_tenant_fee(httpx_mock, gw):
    httpx_mock.add_response(json={"success": True, "requestId": "r1", "data": QUOTE})

    resp = await gw.call("quote", **QUOTE_KW, user_id="u")

    assert resp.success is True
    assert resp.data.settlement_base_usd == "6.0"
    assert resp.data.tenant_fee_usd == "0.1"
    assert resp.data.quote_id == "q1"
    assert resp.data.route.route_id == 7


async def test_place_order_response_has_token_and_settlement_fields_with_optional_memo(
    httpx_mock, gw
):
    httpx_mock.add_response(json={"success": True, "requestId": "r1", "data": PLACE_ORDER})
    httpx_mock.add_response(
        json={"success": True, "requestId": "r2", "data": {**PLACE_ORDER, "memo": "m-1"}}
    )

    without_memo = await gw.call("place_order", quote_id="q1")
    with_memo = await gw.call("place_order", quote_id="q1")

    assert without_memo.data.token_address == "0xtoken"
    assert without_memo.data.settlement_amount == "6.0"
    assert without_memo.data.settlement_amount_base_units == "6000000"
    assert without_memo.data.settlement_currency == "USDC"
    assert without_memo.data.memo is None
    assert with_memo.data.memo == "m-1"


@pytest.mark.parametrize("chain", [None, "solana"])
async def test_organization_balance_has_wallet_address_and_nullable_chain(httpx_mock, gw, chain):
    httpx_mock.add_response(
        json={
            "requestId": "r1",
            "data": {
                "currency": "USDC",
                "availableBalance": "1",
                "totalSpent": "0",
                "pendingSettlement": "0",
                "walletAddress": "0xw",
                "chain": chain,
            },
        }
    )

    resp = await gw.call("get_organization_balance")

    assert resp.data.wallet_address == "0xw"
    assert resp.data.chain == chain


def test_chain_constants_include_stellar_avalanche_and_arc():
    assert gaian.Chain.STELLAR == 148
    assert gaian.Chain.AVALANCHE == 43114
    assert gaian.Chain.ARC == 5042002


@pytest.mark.parametrize("mode", ["missing", "null"])
async def test_user_optional_fields_may_be_missing_or_null(httpx_mock, gw, mode):
    optional = (
        "phoneNumber",
        "phoneCountryCode",
        "rejectReason",
        "addressLine2",
        "state",
        "zipCode",
    )
    user = {k: v for k, v in USER.items() if k not in optional}
    if mode == "null":
        user.update({k: None for k in optional})
    httpx_mock.add_response(json={"requestId": "r1", "data": user})

    resp = await gw.call("get_user_by_id", user_id="usr_1")

    assert resp.data.id == "usr_1"
    assert resp.data.phone_number is None
    assert resp.data.phone_country_code is None
    assert resp.data.reject_reason is None
    assert resp.data.address_line2 is None
    assert resp.data.state is None
    assert resp.data.zip_code is None
