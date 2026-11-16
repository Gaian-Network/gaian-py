import inspect

import pytest

import gaian

from .conftest import Harness, body_of, query_of, sent
from .samples import (
    DIRECT_QUOTE,
    KYC_BODY,
    KYC_KW,
    KYC_SUBMITTED,
    PLACE_ORDER,
    QR_INFO,
    QUOTE,
    USER,
    USER_ORDER,
)

UO = "/api/v2/users/usr_1"
ENV = lambda data: {"requestId": "r1", "data": data}
PAY = lambda data: {"success": True, "requestId": "r1", "data": data}

# (client method, kwargs, http method, path, query, body or None, response json, check on the response)
CASES = {
    "create_user": (
        "create_user",
        {},
        "POST",
        "/api/v2/users",
        {},
        None,
        ENV({"userId": "usr_1"}),
        lambda r: r.data.user_id == "usr_1",
    ),
    "get_user_by_id": (
        "get_user_by_id",
        {"user_id": "usr_1"},
        "GET",
        UO,
        {},
        None,
        ENV(USER),
        lambda r: (r.data.first_name, r.data.kyc_status) == ("Nguyen", "APPROVED"),
    ),
    "get_user_by_wallet": (
        "get_user_by_wallet",
        {"wallet_address": "0xabc"},
        "GET",
        "/api/v2/users/wallet/0xabc",
        {},
        None,
        ENV(USER),
        lambda r: r.data.national_id == "012345678901",
    ),
    "list_user_orders": (
        "list_user_orders",
        {"user_id": "usr_1", "status": "completed", "page": 2, "page_size": 50},
        "GET",
        f"{UO}/orders",
        {"status": "completed", "page": "2", "page_size": "50"},
        None,
        {
            "requestId": "r1",
            "data": [USER_ORDER],
            "pagination": {"page": 2, "pageSize": 50, "totalCount": 1, "totalPages": 1},
        },
        lambda r: (
            (
                r.data[0].order_id,
                r.data[0].payment.paid_at,
                r.pagination.page_size,
                r.pagination.total_count,
            )
            == ("ord_1", None, 50, 1)
        ),
    ),
    "get_markets": (
        "get_markets",
        {"user_id": "usr_1"},
        "GET",
        f"{UO}/markets",
        {},
        None,
        ENV({"markets": {"VN": {"status": "APPROVED"}}}),
        lambda r: r.data.markets["VN"].status == "APPROVED",
    ),
    "get_user_order": (
        "get_user_order",
        {"user_id": "usr_1", "order_id": "ord_1"},
        "GET",
        f"{UO}/orders/ord_1",
        {},
        None,
        ENV(USER_ORDER),
        lambda r: r.data.crypto_transfer.tx_hash == "0xhash",
    ),
    "create_wallet": (
        "create_wallet",
        {"user_id": "usr_1", "address": "0xabc", "chain": "solana"},
        "POST",
        f"{UO}/wallets",
        {},
        {"address": "0xabc", "chain": "solana"},
        ENV({"address": "0xabc", "chain": "solana", "isPrimary": True}),
        lambda r: r.data.is_primary is True,
    ),
    "list_wallets": (
        "list_wallets",
        {"user_id": "usr_1"},
        "GET",
        f"{UO}/wallets",
        {},
        None,
        ENV([{"address": "0xabc", "chain": "solana", "isPrimary": True}]),
        lambda r: r.data[0].address == "0xabc",
    ),
    "submit_kyc": (
        "submit_kyc",
        KYC_KW,
        "POST",
        f"{UO}/kyc",
        {},
        KYC_BODY,
        KYC_SUBMITTED,
        lambda r: r.data.kyc_status == "PROCESSING",
    ),
    "update_kyc": (
        "update_kyc",
        {"user_id": "usr_1", "first_name": "B", "phone_number": "912"},
        "PATCH",
        f"{UO}/kyc",
        {},
        {"firstName": "B", "phoneNumber": "912"},
        ENV(None),
        lambda r: r.data is None,
    ),
    "generate_kyc_link": (
        "generate_kyc_link",
        {"user_id": "usr_1", "callback_url": "https://x.test/cb"},
        "POST",
        f"{UO}/kyc-url",
        {},
        {"callbackUrl": "https://x.test/cb"},
        ENV({"url": "https://kyc.test/s"}),
        lambda r: r.data.url == "https://kyc.test/s",
    ),
    "get_organization_balance": (
        "get_organization_balance",
        {},
        "GET",
        "/api/v2/organization/me/balance",
        {},
        None,
        ENV(
            {
                "currency": "USDC",
                "availableBalance": "100.5",
                "totalSpent": "1",
                "pendingSettlement": "0",
                "walletAddress": "0xw",
                "chain": "solana",
            }
        ),
        lambda r: r.data.available_balance == "100.5",
    ),
    "parse_qr": (
        "parse_qr",
        {"qr_string": "qr", "country": "VN"},
        "POST",
        "/api/v2/parseQr",
        {},
        {"qrString": "qr", "country": "VN"},
        PAY(QR_INFO),
        lambda r: r.data.bank_bin == "970436",
    ),
    "quote": (
        "quote",
        {
            "qr_string": "qr",
            "amount": 150000,
            "chain_id": 101,
            "settlement_currency": "USDC",
            "user_id": "usr_1",
        },
        "POST",
        "/api/v2/quote",
        {},
        {
            "qrString": "qr",
            "amount": 150000,
            "chainId": 101,
            "settlementCurrency": "USDC",
            "userId": "usr_1",
        },
        PAY(QUOTE),
        lambda r: (
            (r.data.quote_id, r.data.fiat_amount, r.data.qr_info.country) == ("q1", 150000, "VN")
        ),
    ),
    "quote_direct": (
        "quote_direct",
        {
            "account_number": "0123456789",
            "code": "970436",
            "amount": 150000,
            "country": "VN",
            "chain_id": 101,
            "settlement_currency": "USDC",
            "user_id": "usr_1",
            "beneficiary_name": "NGUYEN VAN A",
        },
        "POST",
        "/api/v2/quote/direct",
        {},
        {
            "accountNumber": "0123456789",
            "code": "970436",
            "amount": 150000,
            "country": "VN",
            "chainId": 101,
            "settlementCurrency": "USDC",
            "userId": "usr_1",
            "beneficiaryName": "NGUYEN VAN A",
        },
        PAY(DIRECT_QUOTE),
        lambda r: r.data.qr_info.account_number == "0123456789",
    ),
    "quote_prefund": (
        "quote_prefund",
        {"qr_string": "qr", "amount": 150000, "settlement_currency": "USDC", "user_id": "usr_1"},
        "POST",
        "/api/v2/quote/prefund",
        {},
        {"qrString": "qr", "amount": 150000, "settlementCurrency": "USDC", "userId": "usr_1"},
        PAY(QUOTE),
        lambda r: r.data.quote_id == "q1",
    ),
    "quote_direct_prefund": (
        "quote_direct_prefund",
        {
            "account_number": "0123456789",
            "code": "970436",
            "amount": 150000,
            "country": "VN",
            "settlement_currency": "USDC",
            "user_id": "usr_1",
        },
        "POST",
        "/api/v2/quote/direct/prefund",
        {},
        {
            "accountNumber": "0123456789",
            "code": "970436",
            "amount": 150000,
            "country": "VN",
            "settlementCurrency": "USDC",
            "userId": "usr_1",
        },
        PAY(DIRECT_QUOTE),
        lambda r: r.data.quote_id == "q1",
    ),
    "place_order": (
        "place_order",
        {"quote_id": "q1"},
        "POST",
        "/api/v2/orders",
        {},
        {"quoteId": "q1"},
        PAY(PLACE_ORDER),
        lambda r: (r.data.order_id, r.data.encoded_transaction) == ("ord_1", "base64tx"),
    ),
    "place_prefunded_order": (
        "place_prefunded_order",
        {"quote_id": "q1"},
        "POST",
        "/api/v2/orders/prefund",
        {},
        {"quoteId": "q1"},
        PAY({"orderId": "ord_1", "status": 10, "statusLabel": "completed"}),
        lambda r: r.data.status == 10,
    ),
    "verify_order": (
        "verify_order",
        {"order_id": "ord_1", "transaction_hash": "0xhash"},
        "POST",
        "/api/v2/orders/ord_1/verify",
        {},
        {"transactionHash": "0xhash"},
        PAY(
            {
                "orderId": "ord_1",
                "status": 1,
                "statusLabel": "verified",
                "transactionHash": "0xhash",
                "message": "ok",
            }
        ),
        lambda r: (r.data.status, r.data.transaction_hash) == (1, "0xhash"),
    ),
    "get_order_status": (
        "get_order_status",
        {"order_id": "ord_1"},
        "GET",
        "/api/v2/orders/ord_1",
        {},
        None,
        PAY(
            {
                "orderId": "ord_1",
                "status": 10,
                "statusLabel": "completed",
                "chainId": 101,
                "fiatAmount": 150000,
                "fiatCurrency": "VND",
                "settlementAmount": "6.0",
                "settlementCurrency": "USDC",
                "exchangeRate": "25000",
                "createdAt": "2026-11-16T10:00:00Z",
                "updatedAt": "2026-11-16T10:05:00Z",
            }
        ),
        lambda r: (
            (r.data.status, r.data.deposit_address, r.data.transaction_hash) == (10, None, None)
        ),
    ),
    "list_banks": (
        "list_banks",
        {"country": "VN"},
        "GET",
        "/api/v2/banks",
        {"country": "VN"},
        None,
        PAY({"country": "VN", "banks": [{"id": 1, "code": "970436", "name": "Vietcombank"}]}),
        lambda r: r.data.banks[0].code == "970436",
    ),
    "verify_account": (
        "verify_account",
        {"account_number": "0123456789", "code": "970436", "country": "VN"},
        "POST",
        "/api/v2/accounts/verify",
        {},
        {"accountNumber": "0123456789", "code": "970436", "country": "VN"},
        PAY(
            {
                "country": "VN",
                "accountNumber": "0123456789",
                "code": "970436",
                "valid": False,
                "accountName": None,
            }
        ),
        lambda r: r.data.valid is False and r.data.account_name is None,
    ),
}

ALL_METHODS = sorted(
    list(CASES)
    + [
        "import_shared_kyc",
        "get_market_requirements",
        "get_payment_methods",
        "get_user_limits",
        "get_exchange_rates",
    ]
)


@pytest.mark.parametrize("name", list(CASES))
async def test_existing_endpoint_sends_expected_request_and_parses_response(httpx_mock, gw, name):
    method, kwargs, http_method, path, query, body, response, check = CASES[name]
    httpx_mock.add_response(json=response)

    resp = await gw.call(method, **kwargs)

    req = sent(httpx_mock)
    assert (req.method, req.url.host, req.url.path) == (http_method, "gw.test", path)
    assert query_of(req) == query
    if body is None:
        assert req.content in (b"", b"{}")
    else:
        assert body_of(req) == body
    assert resp.request_id == "r1"
    assert check(resp)


async def test_payment_envelopes_carry_success_flag(httpx_mock, gw):
    httpx_mock.add_response(json=PAY({"country": "VN", "banks": []}))

    resp = await gw.call("list_banks", country="VN")

    assert resp.success is True


@pytest.mark.parametrize("flavor", ["sync", "async"])
def test_client_exposes_every_method_with_matching_sync_or_async_kind(flavor):
    h = Harness(flavor)
    for name in ALL_METHODS:
        fn = getattr(h.client, name)
        assert callable(fn), name
        assert inspect.iscoroutinefunction(fn) == (flavor == "async"), name


@pytest.mark.parametrize(
    "env, host",
    [
        (None, "sandbox.gaian.network"),
        (gaian.Environment.SANDBOX, "sandbox.gaian.network"),
        (gaian.Environment.PRODUCTION, "api.gaian.network"),
    ],
)
async def test_environment_selects_base_url(httpx_mock, make_harness, env, host):
    httpx_mock.add_response(json=ENV({"userId": "usr_1"}))
    opts = {"base_url": None}
    if env is not None:
        opts["environment"] = env
    gw = make_harness(**opts)

    await gw.call("create_user")

    assert sent(httpx_mock).url.host == host
