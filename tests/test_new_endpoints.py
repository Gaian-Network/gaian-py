import pytest

import gaian

from .conftest import body_of, query_of, sent

HOST = "gw.test"


async def test_import_shared_kyc_posts_share_token_only(httpx_mock, gw):
    httpx_mock.add_response(
        json={"requestId": "r1", "data": {"sessionId": "sess_1", "status": "In Review"}}
    )

    resp = await gw.call("import_shared_kyc", user_id="usr_1", share_token="tok")

    req = sent(httpx_mock)
    assert (req.method, req.url.host, req.url.path) == (
        "POST",
        HOST,
        "/api/v2/users/usr_1/kyc/import-shared",
    )
    assert body_of(req) == {"shareToken": "tok"}
    assert resp.request_id == "r1"
    assert resp.data.session_id == "sess_1"
    assert resp.data.status == "In Review"


async def test_import_shared_kyc_surfaces_409_as_conflict(httpx_mock, gw):
    httpx_mock.add_response(status_code=409, json={"message": "already imported"})

    with pytest.raises(gaian.GaianAPIError) as info:
        await gw.call("import_shared_kyc", user_id="usr_1", share_token="tok")

    assert info.value.code == "CONFLICT"
    assert gaian.is_conflict(info.value)


async def test_get_market_requirements_parses_per_country_map(httpx_mock, gw):
    httpx_mock.add_response(
        json={
            "requestId": "r1",
            "data": {
                "markets": {
                    "VN": {
                        "requiredFields": ["kycReport", "phoneNumber"],
                        "missingFields": ["phoneNumber"],
                    }
                }
            },
        }
    )

    resp = await gw.call("get_market_requirements", user_id="usr_1")

    req = sent(httpx_mock)
    assert (req.method, req.url.path) == ("GET", "/api/v2/users/usr_1/markets/requirements")
    assert resp.data.markets["VN"].required_fields == ["kycReport", "phoneNumber"]
    assert resp.data.markets["VN"].missing_fields == ["phoneNumber"]


async def test_get_payment_methods_parses_array_with_optional_fields(httpx_mock, gw):
    httpx_mock.add_response(
        json={
            "requestId": "r1",
            "data": [
                {"method": "QR_PAYMENT", "name": "QR", "status": "APPROVED"},
                {
                    "method": "CARD_PAYMENT",
                    "name": "Card",
                    "status": "REJECTED",
                    "rejectReason": "doc",
                    "action": "resubmit",
                },
            ],
        }
    )

    resp = await gw.call("get_payment_methods", user_id="usr_1")

    req = sent(httpx_mock)
    assert (req.method, req.url.path) == ("GET", "/api/v2/users/usr_1/payment-methods")
    first, second = resp.data
    assert (first.method, first.status, first.reject_reason, first.action) == (
        "QR_PAYMENT",
        "APPROVED",
        None,
        None,
    )
    assert (second.method, second.status, second.reject_reason, second.action) == (
        "CARD_PAYMENT",
        "REJECTED",
        "doc",
        "resubmit",
    )


async def test_get_user_limits_sends_query_and_parses_nested_numbers(httpx_mock, gw):
    httpx_mock.add_response(
        json={
            "success": True,
            "requestId": "r1",
            "data": {
                "userId": None,
                "daily": {
                    "spentUsd": 10.5,
                    "windowStart": "2026-11-16T00:00:00Z",
                    "windowEnd": "2026-11-17T00:00:00Z",
                },
                "velocity": {
                    "enabled": True,
                    "maxPerWindow": 5,
                    "windowSeconds": 3600,
                    "usedInWindow": 1,
                    "remaining": 4,
                    "retryAfterSeconds": 0,
                },
                "countries": [
                    {
                        "country": "VN",
                        "supported": True,
                        "kycVerified": True,
                        "canTransact": True,
                        "maxPerDayUsd": 1000,
                        "dailyRemainingUsd": 989.5,
                        "weekly": {
                            "capUsd": 5000,
                            "spentUsd": 10.5,
                            "remainingUsd": 4989.5,
                            "windowStart": "a",
                            "windowEnd": "b",
                        },
                        "maxNextTransactionUsd": 500,
                    },
                    {
                        "country": "TH",
                        "supported": False,
                        "kycVerified": False,
                        "canTransact": False,
                        "maxNextTransactionUsd": 0,
                    },
                ],
            },
        }
    )

    resp = await gw.call("get_user_limits", user_id="usr_1", country="VN")

    req = sent(httpx_mock)
    assert (req.method, req.url.path) == ("GET", "/api/v2/limits/user")
    assert query_of(req) == {"userId": "usr_1", "country": "VN"}
    assert req.content == b""
    assert resp.success is True
    assert resp.data.user_id is None
    assert resp.data.daily.spent_usd == 10.5
    assert resp.data.velocity.remaining == 4
    vn, th = resp.data.countries
    assert vn.weekly.remaining_usd == 4989.5
    assert vn.max_per_day_usd == 1000
    assert th.weekly is None
    assert th.max_per_day_usd is None


async def test_get_exchange_rates_sends_query_and_keeps_rate_as_string(httpx_mock, gw):
    httpx_mock.add_response(
        json={
            "success": True,
            "requestId": "r1",
            "data": {
                "indicativeOnly": True,
                "rates": [
                    {
                        "country": "VN",
                        "fiatCurrency": "VND",
                        "settlementCurrency": "USDC",
                        "routeId": 7,
                        "exchangeRate": "25400.1234",
                        "capturedAt": "2026-11-16T10:00:00Z",
                    }
                ],
            },
        }
    )

    resp = await gw.call("get_exchange_rates", country="VN", settlement_currency="USDC")

    req = sent(httpx_mock)
    assert (req.method, req.url.path) == ("GET", "/api/v2/exchange-rate")
    assert query_of(req) == {"country": "VN", "settlementCurrency": "USDC"}
    assert resp.data.indicative_only is True
    rate = resp.data.rates[0]
    assert rate.exchange_rate == "25400.1234"
    assert isinstance(rate.exchange_rate, str)
    assert rate.route_id == 7
    assert rate.fiat_currency == "VND"
