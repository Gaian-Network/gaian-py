from __future__ import annotations

from typing import Optional

from ._core import AsyncCore, SyncCore
from ._models import (
    CalculateExchangeRequest,
    ExchangeInfo,
    Order,
    ParsedQRInfo,
    PlaceOrderRequest,
    PlaceOrderResponse,
    PlacePrefundedOrderRequest,
    VerifyOrderResult,
)


class PaymentService:
    def __init__(self, core: SyncCore) -> None:
        self._c = core

    def place_order(self, req: PlaceOrderRequest) -> PlaceOrderResponse:
        data = self._c.payment_post(
            "/api/v1/placeOrder",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return PlaceOrderResponse.model_validate(data)

    def place_prefunded_order(self, req: PlacePrefundedOrderRequest) -> PlaceOrderResponse:
        data = self._c.payment_post(
            "/api/v1/placeOrder/prefund",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return PlaceOrderResponse.model_validate(data)

    def verify_order(self, order_id: str, transaction_proof: str) -> VerifyOrderResult:
        data = self._c.payment_post(
            "/api/v1/verifyOrder",
            json={"orderId": order_id, "transactionProof": transaction_proof},
        )
        return VerifyOrderResult.model_validate(data)

    def get_order_status(self, order_id: str) -> Order:
        data = self._c.payment_get("/api/v1/status", params={"orderId": order_id})
        return Order.model_validate(data)

    def parse_qr(self, qr_string: str, country: Optional[str] = None) -> ParsedQRInfo:
        body: dict = {"qrString": qr_string}
        if country:
            body["country"] = country
        data = self._c.payment_post("/api/v1/parseQr", json=body)
        return ParsedQRInfo.model_validate(data["qrInfo"])

    def calculate_exchange(self, req: CalculateExchangeRequest) -> ExchangeInfo:
        data = self._c.payment_post(
            "/api/v1/calculateExchange",
            json=req.model_dump(by_alias=True),
        )
        return ExchangeInfo.model_validate(data["exchangeInfo"])


class AsyncPaymentService:
    def __init__(self, core: AsyncCore) -> None:
        self._c = core

    async def place_order(self, req: PlaceOrderRequest) -> PlaceOrderResponse:
        data = await self._c.payment_post(
            "/api/v1/placeOrder",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return PlaceOrderResponse.model_validate(data)

    async def place_prefunded_order(self, req: PlacePrefundedOrderRequest) -> PlaceOrderResponse:
        data = await self._c.payment_post(
            "/api/v1/placeOrder/prefund",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return PlaceOrderResponse.model_validate(data)

    async def verify_order(self, order_id: str, transaction_proof: str) -> VerifyOrderResult:
        data = await self._c.payment_post(
            "/api/v1/verifyOrder",
            json={"orderId": order_id, "transactionProof": transaction_proof},
        )
        return VerifyOrderResult.model_validate(data)

    async def get_order_status(self, order_id: str) -> Order:
        data = await self._c.payment_get("/api/v1/status", params={"orderId": order_id})
        return Order.model_validate(data)

    async def parse_qr(self, qr_string: str, country: Optional[str] = None) -> ParsedQRInfo:
        body: dict = {"qrString": qr_string}
        if country:
            body["country"] = country
        data = await self._c.payment_post("/api/v1/parseQr", json=body)
        return ParsedQRInfo.model_validate(data["qrInfo"])

    async def calculate_exchange(self, req: CalculateExchangeRequest) -> ExchangeInfo:
        data = await self._c.payment_post(
            "/api/v1/calculateExchange",
            json=req.model_dump(by_alias=True),
        )
        return ExchangeInfo.model_validate(data["exchangeInfo"])
