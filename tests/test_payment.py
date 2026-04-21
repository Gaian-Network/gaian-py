import pytest
from pytest_httpx import HTTPXMock

import gaian

PMT_BASE = "https://dev-payments.gaian-dev.network"


def make_client(pmt_base: str = PMT_BASE):
    return gaian.GaianClient(
        api_key="test-key",
        _user_base_url="https://dev-user.gaian-dev.network",
        _payment_base_url=pmt_base,
    )


ORDER_RESPONSE = {
    "orderId": "ord_001",
    "status": "awaiting_crypto_transfer",
    "fiatAmount": 100000.0,
    "fiatCurrency": "VND",
    "cryptoAmount": 4.0,
    "cryptoCurrency": "USDC",
    "exchangeRate": 25000.0,
    "routeId": 1,
}

FULL_ORDER = {
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


def test_place_order(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{PMT_BASE}/api/v1/placeOrder",
        json=ORDER_RESPONSE,
    )
    with make_client() as c:
        order = c.payment.place_order(gaian.PlaceOrderRequest(
            qr_string="00020101...",
            amount=100000,
            crypto_currency=gaian.CryptoCurrency.USDC,
            from_address="0xABC",
            fiat_currency=gaian.FiatCurrency.VND,
            chain=gaian.Chain.SOLANA,
        ))
    assert order.order_id == "ord_001"
    assert order.status == gaian.OrderStatus.AWAITING_CRYPTO_TRANSFER


def test_place_prefunded_order(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{PMT_BASE}/api/v1/placeOrder/prefund",
        json={**ORDER_RESPONSE, "isPrefunded": True},
    )
    with make_client() as c:
        order = c.payment.place_prefunded_order(gaian.PlacePrefundedOrderRequest(
            qr_string="00020101...",
            amount=100000,
            crypto_currency=gaian.CryptoCurrency.USDC,
            from_address="0xABC",
            fiat_currency=gaian.FiatCurrency.VND,
        ))
    assert order.is_prefunded is True


def test_verify_order(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{PMT_BASE}/api/v1/verifyOrder",
        json={
            "orderId": "ord_001",
            "status": "verified",
            "transactionHash": "0xTX",
            "message": "ok",
            "bankTransferStatus": "queued",
        },
    )
    with make_client() as c:
        result = c.payment.verify_order("ord_001", "0xTX")
    assert result.status == gaian.OrderStatus.VERIFIED
    assert result.bank_transfer_status == "queued"


def test_get_order_status(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{PMT_BASE}/api/v1/status?orderId=ord_001",
        json=FULL_ORDER,
    )
    with make_client() as c:
        order = c.payment.get_order_status("ord_001")
    assert order.status == gaian.OrderStatus.COMPLETED
    assert order.order_id == "ord_001"


def test_parse_qr(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{PMT_BASE}/api/v1/parseQr",
        json={
            "success": True,
            "qrInfo": {
                "isValid": True,
                "encodedString": "00020101...",
                "country": "VN",
                "beneficiaryName": "NGUYEN VAN A",
                "amount": 500000.0,
                "currency": "VND",
            },
            "timestamp": "2024-01-01T00:00:00Z",
        },
    )
    with make_client() as c:
        info = c.payment.parse_qr("00020101...")
    assert info.is_valid is True
    assert info.country == "VN"
    assert info.amount == 500000.0


def test_calculate_exchange(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        method="POST",
        url=f"{PMT_BASE}/api/v1/calculateExchange",
        json={
            "success": True,
            "exchangeInfo": {
                "fiatAmount": 100000.0,
                "fiatCurrency": "VND",
                "cryptoAmount": "4.0",
                "cryptoCurrency": "USDC",
                "exchangeRate": "25000",
                "chain": "Solana",
                "token": "USDC",
                "feeAmount": "0.05",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        },
    )
    with make_client() as c:
        info = c.payment.calculate_exchange(gaian.CalculateExchangeRequest(
            amount=100000,
            country="VN",
            chain=gaian.Chain.SOLANA,
            token=gaian.CryptoCurrency.USDC,
        ))
    assert info.crypto_amount == "4.0"
    assert info.exchange_rate == "25000"


async def test_get_order_status_async(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{PMT_BASE}/api/v1/status?orderId=ord_001",
        json=FULL_ORDER,
    )
    async with gaian.AsyncGaianClient(
        api_key="test-key",
        _user_base_url="https://dev-user.gaian-dev.network",
        _payment_base_url=PMT_BASE,
    ) as c:
        order = await c.payment.get_order_status("ord_001")
    assert order.status == gaian.OrderStatus.COMPLETED
