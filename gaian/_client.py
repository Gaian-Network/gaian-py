from __future__ import annotations

from enum import Enum
from typing import Any, Optional

import httpx

from ._core import AsyncCore, SyncCore
from ._payment import AsyncPaymentService, PaymentService
from ._policy import AsyncPolicyService, PolicyService
from ._tenant import AsyncTenantService, TenantService
from ._user import AsyncUserService, UserService

_SANDBOX_USER = "https://dev-user.gaian-dev.network"
_SANDBOX_PAYMENT = "https://dev-payments.gaian-dev.network"
_PROD_USER = "https://user.gaian-dev.network"
_PROD_PAYMENT = "https://payments.gaian-dev.network"


class Environment(str, Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class GaianClient:
    """Synchronous Gaian API client.

    Usage::

        with GaianClient(api_key="...", env=Environment.SANDBOX) as client:
            user = client.user.register("0xWallet")

    Or without context manager (remember to call close())::

        client = GaianClient(api_key="...", env=Environment.SANDBOX)
        user = client.user.register("0xWallet")
        client.close()
    """

    def __init__(
        self,
        api_key: str,
        env: Environment = Environment.SANDBOX,
        *,
        http_client: Optional[httpx.Client] = None,
        timeout: float = 30.0,
        _user_base_url: Optional[str] = None,
        _payment_base_url: Optional[str] = None,
    ) -> None:
        user_url = _user_base_url or (
            _SANDBOX_USER if env == Environment.SANDBOX else _PROD_USER
        )
        pmt_url = _payment_base_url or (
            _SANDBOX_PAYMENT if env == Environment.SANDBOX else _PROD_PAYMENT
        )
        core = SyncCore(api_key, user_url, pmt_url, client=http_client, timeout=timeout)
        self.user = UserService(core)
        self.payment = PaymentService(core)
        self.tenant = TenantService(core)
        self.policy = PolicyService(core)
        self._core = core

    def close(self) -> None:
        self._core.close()

    def __enter__(self) -> "GaianClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class AsyncGaianClient:
    """Asynchronous Gaian API client.

    Usage::

        async with AsyncGaianClient(api_key="...", env=Environment.SANDBOX) as client:
            user = await client.user.register("0xWallet")
    """

    def __init__(
        self,
        api_key: str,
        env: Environment = Environment.SANDBOX,
        *,
        http_client: Optional[httpx.AsyncClient] = None,
        timeout: float = 30.0,
        _user_base_url: Optional[str] = None,
        _payment_base_url: Optional[str] = None,
    ) -> None:
        user_url = _user_base_url or (
            _SANDBOX_USER if env == Environment.SANDBOX else _PROD_USER
        )
        pmt_url = _payment_base_url or (
            _SANDBOX_PAYMENT if env == Environment.SANDBOX else _PROD_PAYMENT
        )
        core = AsyncCore(api_key, user_url, pmt_url, client=http_client, timeout=timeout)
        self.user = AsyncUserService(core)
        self.payment = AsyncPaymentService(core)
        self.tenant = AsyncTenantService(core)
        self.policy = AsyncPolicyService(core)
        self._core = core

    async def aclose(self) -> None:
        await self._core.aclose()

    async def __aenter__(self) -> "AsyncGaianClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
