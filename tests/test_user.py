import pytest
import httpx
from pytest_httpx import HTTPXMock

import gaian

USER_BASE = "https://dev-user.gaian-dev.network"


def make_client(user_base: str = USER_BASE):
    return gaian.GaianClient(
        api_key="test-key",
        _user_base_url=user_base,
        _payment_base_url="https://dev-payments.gaian-dev.network",
    )


USER_PAYLOAD = {
    "id": 42,
    "walletAddress": "0xABC",
    "kycStatus": "not_started",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z",
}


# ── Register ──────────────────────────────────────────────────────────────────

def test_register(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{USER_BASE}/api/v1/user/register",
        json={"status": "success", "message": "created", "user": USER_PAYLOAD},
    )
    with make_client() as c:
        user = c.user.register("0xABC")
    assert user.id == 42
    assert user.kyc_status == gaian.KYCStatus.NOT_STARTED


def test_register_conflict(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{USER_BASE}/api/v1/user/register",
        status_code=409,
        json={"status": "error", "message": "user already exists"},
    )
    with make_client() as c:
        with pytest.raises(gaian.GaianAPIError) as exc:
            c.user.register("0xABC")
    assert gaian.is_conflict(exc.value)


# ── Get ───────────────────────────────────────────────────────────────────────

def test_get_by_id(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{USER_BASE}/api/v1/users/42",
        json={"status": "success", "data": USER_PAYLOAD},
    )
    with make_client() as c:
        user = c.user.get_by_id(42)
    assert user.id == 42


def test_get_by_wallet(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{USER_BASE}/api/v1/users?walletAddress=0xABC",
        json={"status": "success", "data": {**USER_PAYLOAD, "kycStatus": "approved"}},
    )
    with make_client() as c:
        user = c.user.get_by_wallet("0xABC")
    assert user.kyc_status == gaian.KYCStatus.APPROVED


def test_get_not_found(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{USER_BASE}/api/v1/users/999",
        status_code=404,
        json={"status": "error", "message": "not found"},
    )
    with make_client() as c:
        with pytest.raises(gaian.GaianAPIError) as exc:
            c.user.get_by_id(999)
    assert gaian.is_not_found(exc.value)


# ── Markets ───────────────────────────────────────────────────────────────────

def test_get_markets(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{USER_BASE}/api/v1/users/markets?walletAddress=0xABC",
        json={
            "status": "success",
            "data": {
                "markets": {
                    "VN": {"status": "approved"},
                    "PH": {"status": "pending"},
                }
            },
        },
    )
    with make_client() as c:
        markets = c.user.get_markets("0xABC")
    assert markets["VN"].status == gaian.MarketStatus.APPROVED
    assert markets["PH"].status == gaian.MarketStatus.PENDING


# ── Orders ────────────────────────────────────────────────────────────────────

ORDER_ITEM = {
    "id": 1,
    "orderId": "ord_001",
    "status": "completed",
    "fiatAmount": 100000.0,
    "fiatCurrency": "VND",
    "cryptoAmount": 4.0,
    "cryptoCurrency": "USDC",
    "exchangeRate": 25000.0,
    "paymentMethod": "crypto",
    "expiresAt": "2024-01-01T01:00:00Z",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:30:00Z",
}

ORDERS_RESPONSE = {
    "status": "success",
    "data": {
        "user": USER_PAYLOAD,
        "orders": {
            "items": [ORDER_ITEM],
            "pagination": {
                "page": 1, "limit": 20, "total": 1,
                "totalPages": 1, "hasNext": False, "hasPrev": False,
            },
        },
    },
}


def test_list_orders_by_wallet(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{USER_BASE}/api/v1/users/wallet/0xABC/orders?page=1&limit=20",
        json=ORDERS_RESPONSE,
    )
    with make_client() as c:
        result = c.user.list_orders_by_wallet("0xABC")
    assert len(result.items) == 1
    assert result.items[0].order_id == "ord_001"
    assert result.pagination.total == 1


# ── KYC ───────────────────────────────────────────────────────────────────────

def test_generate_kyc_link(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{USER_BASE}/api/v1/kyc/link",
        json={"status": True, "message": "ok", "websdkUrl": "https://kyc.example.com/abc"},
    )
    with make_client() as c:
        url = c.user.generate_kyc_link("0xABC")
    assert url == "https://kyc.example.com/abc"


# ── Async ─────────────────────────────────────────────────────────────────────

async def test_register_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{USER_BASE}/api/v1/user/register",
        json={"status": "success", "message": "created", "user": USER_PAYLOAD},
    )
    async with gaian.AsyncGaianClient(
        api_key="test-key",
        _user_base_url=USER_BASE,
        _payment_base_url="https://dev-payments.gaian-dev.network",
    ) as c:
        user = await c.user.register("0xABC")
    assert user.id == 42
