from pytest_httpx import HTTPXMock

import gaian

USER_BASE = "https://dev-user.gaian-dev.network"
PMT_BASE = "https://dev-payments.gaian-dev.network"


def make_client():
    return gaian.GaianClient(
        api_key="test-key",
        _user_base_url=USER_BASE,
        _payment_base_url=PMT_BASE,
    )


def test_get_balance(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{USER_BASE}/api/v1/tenant/balance?currency=USDC",
        json={"currency": "USDC", "availableBalance": 100.5, "walletAddress": "0xT", "chain": "Solana"},
    )
    with make_client() as c:
        bal = c.tenant.get_balance(gaian.CryptoCurrency.USDC)
    assert bal.available_balance == 100.5
    assert bal.chain == gaian.Chain.SOLANA


def test_get_total_spent(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{USER_BASE}/api/v1/tenant/total-spent",
        json={"totalSpent": 1234.56, "limit": 4000.0},
    )
    with make_client() as c:
        spend = c.tenant.get_total_spent()
    assert spend.total_spent == 1234.56
    assert spend.limit == 4000.0


def test_check_policy(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{PMT_BASE}/api/v1/checkPolicy?walletAddress=0xABC&countryCode=VN",
        json={
            "isAllowed": True,
            "routeId": 1,
            "limits": {"perTransaction": 500.0, "perDay": 5000.0},
            "tier": "KYC",
        },
    )
    with make_client() as c:
        policy = c.policy.check_policy("0xABC", "VN")
    assert policy.is_allowed is True
    assert policy.tier == gaian.PolicyTier.KYC
    assert policy.limits.per_transaction == 500.0


def test_check_policy_not_allowed(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{PMT_BASE}/api/v1/checkPolicy?walletAddress=0xABC&countryCode=VN",
        json={
            "isAllowed": False,
            "routeId": 1,
            "limits": {"perTransaction": 0.0, "perDay": 0.0},
            "tier": "NON_KYC",
            "reason": "kyc_required",
        },
    )
    with make_client() as c:
        policy = c.policy.check_policy("0xABC", "VN")
    assert policy.is_allowed is False
    assert policy.reason == "kyc_required"
