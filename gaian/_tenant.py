from __future__ import annotations

from typing import Optional

from ._core import AsyncCore, SyncCore
from ._models import CryptoCurrency, TenantBalance, TenantSpend


class TenantService:
    def __init__(self, core: SyncCore) -> None:
        self._c = core

    def get_balance(self, currency: Optional[CryptoCurrency] = None) -> TenantBalance:
        params = {"currency": currency.value} if currency else {}
        data = self._c.user_get("/api/v1/tenant/balance", params=params)
        return TenantBalance.model_validate(data)

    def get_total_spent(self) -> TenantSpend:
        data = self._c.user_get("/api/v1/tenant/total-spent")
        return TenantSpend.model_validate(data)


class AsyncTenantService:
    def __init__(self, core: AsyncCore) -> None:
        self._c = core

    async def get_balance(self, currency: Optional[CryptoCurrency] = None) -> TenantBalance:
        params = {"currency": currency.value} if currency else {}
        data = await self._c.user_get("/api/v1/tenant/balance", params=params)
        return TenantBalance.model_validate(data)

    async def get_total_spent(self) -> TenantSpend:
        data = await self._c.user_get("/api/v1/tenant/total-spent")
        return TenantSpend.model_validate(data)
