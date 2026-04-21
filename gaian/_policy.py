from __future__ import annotations

from ._core import AsyncCore, SyncCore
from ._models import PolicyResult


class PolicyService:
    def __init__(self, core: SyncCore) -> None:
        self._c = core

    def check_policy(self, wallet_address: str, country_code: str) -> PolicyResult:
        data = self._c.payment_get(
            "/api/v1/checkPolicy",
            params={"walletAddress": wallet_address, "countryCode": country_code},
        )
        return PolicyResult.model_validate(data)


class AsyncPolicyService:
    def __init__(self, core: AsyncCore) -> None:
        self._c = core

    async def check_policy(self, wallet_address: str, country_code: str) -> PolicyResult:
        data = await self._c.payment_get(
            "/api/v1/checkPolicy",
            params={"walletAddress": wallet_address, "countryCode": country_code},
        )
        return PolicyResult.model_validate(data)
