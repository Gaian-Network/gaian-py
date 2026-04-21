from __future__ import annotations

from typing import Optional

from ._core import AsyncCore, SyncCore
from ._models import (
    KYCStatus,
    MarketInfo,
    Order,
    OrderList,
    OrderStatus,
    SubmitKYCRequest,
    User,
)


class UserService:
    def __init__(self, core: SyncCore) -> None:
        self._c = core

    # ── Register ──────────────────────────────────────────────────────────────

    def register(self, wallet_address: str) -> User:
        data = self._c.user_post(
            "/api/v1/user/register", json={"walletAddress": wallet_address}
        )
        return User.model_validate(data["user"])

    # ── Get ───────────────────────────────────────────────────────────────────

    def get_by_id(self, user_id: int) -> User:
        data = self._c.user_get(f"/api/v1/users/{user_id}")
        return User.model_validate(data["data"])

    def get_by_wallet(self, wallet_address: str) -> User:
        data = self._c.user_get("/api/v1/users", params={"walletAddress": wallet_address})
        return User.model_validate(data["data"])

    # ── Markets ───────────────────────────────────────────────────────────────

    def get_markets(self, wallet_address: str) -> dict[str, MarketInfo]:
        data = self._c.user_get("/api/v1/users/markets", params={"walletAddress": wallet_address})
        return {
            code: MarketInfo.model_validate(info)
            for code, info in data["data"]["markets"].items()
        }

    # ── Orders ────────────────────────────────────────────────────────────────

    def list_orders_by_wallet(
        self,
        wallet_address: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[OrderStatus] = None,
    ) -> OrderList:
        params: dict = {"page": page, "limit": limit}
        if status:
            params["status"] = status.value
        data = self._c.user_get(
            f"/api/v1/users/wallet/{wallet_address}/orders", params=params
        )
        return OrderList.model_validate(data["data"]["orders"])

    def list_orders_by_identifier(
        self,
        identifier: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[OrderStatus] = None,
    ) -> OrderList:
        params: dict = {"page": page, "limit": limit}
        if status:
            params["status"] = status.value
        data = self._c.user_get(f"/api/v1/users/{identifier}/orders", params=params)
        return OrderList.model_validate(data["data"]["orders"])

    # ── KYC ───────────────────────────────────────────────────────────────────

    def generate_kyc_link(self, wallet_address: str) -> str:
        data = self._c.user_post(
            "/api/v1/kyc/link", json={"walletAddress": wallet_address}
        )
        return data["websdkUrl"]

    def submit_kyc(self, req: SubmitKYCRequest) -> KYCStatus:
        data = self._c.user_post(
            "/api/v1/submit-kyc-information",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return KYCStatus(data["data"]["kycStatus"])


class AsyncUserService:
    def __init__(self, core: AsyncCore) -> None:
        self._c = core

    async def register(self, wallet_address: str) -> User:
        data = await self._c.user_post(
            "/api/v1/user/register", json={"walletAddress": wallet_address}
        )
        return User.model_validate(data["user"])

    async def get_by_id(self, user_id: int) -> User:
        data = await self._c.user_get(f"/api/v1/users/{user_id}")
        return User.model_validate(data["data"])

    async def get_by_wallet(self, wallet_address: str) -> User:
        data = await self._c.user_get("/api/v1/users", params={"walletAddress": wallet_address})
        return User.model_validate(data["data"])

    async def get_markets(self, wallet_address: str) -> dict[str, MarketInfo]:
        data = await self._c.user_get(
            "/api/v1/users/markets", params={"walletAddress": wallet_address}
        )
        return {
            code: MarketInfo.model_validate(info)
            for code, info in data["data"]["markets"].items()
        }

    async def list_orders_by_wallet(
        self,
        wallet_address: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[OrderStatus] = None,
    ) -> OrderList:
        params: dict = {"page": page, "limit": limit}
        if status:
            params["status"] = status.value
        data = await self._c.user_get(
            f"/api/v1/users/wallet/{wallet_address}/orders", params=params
        )
        return OrderList.model_validate(data["data"]["orders"])

    async def list_orders_by_identifier(
        self,
        identifier: str,
        page: int = 1,
        limit: int = 20,
        status: Optional[OrderStatus] = None,
    ) -> OrderList:
        params: dict = {"page": page, "limit": limit}
        if status:
            params["status"] = status.value
        data = await self._c.user_get(f"/api/v1/users/{identifier}/orders", params=params)
        return OrderList.model_validate(data["data"]["orders"])

    async def generate_kyc_link(self, wallet_address: str) -> str:
        data = await self._c.user_post(
            "/api/v1/kyc/link", json={"walletAddress": wallet_address}
        )
        return data["websdkUrl"]

    async def submit_kyc(self, req: SubmitKYCRequest) -> KYCStatus:
        data = await self._c.user_post(
            "/api/v1/submit-kyc-information",
            json=req.model_dump(by_alias=True, exclude_none=True),
        )
        return KYCStatus(data["data"]["kycStatus"])
