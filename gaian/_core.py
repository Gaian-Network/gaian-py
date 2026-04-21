from __future__ import annotations

from typing import Any, Optional

import httpx

from ._errors import GaianAPIError

_DEFAULT_TIMEOUT = 30.0


class SyncCore:
    def __init__(
        self,
        api_key: str,
        user_base_url: str,
        payment_base_url: str,
        client: Optional[httpx.Client] = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self.user_base_url = user_base_url
        self.payment_base_url = payment_base_url
        self._headers = {"x-api-key": api_key}
        self._client = client or httpx.Client(timeout=timeout)
        self._owned = client is None

    def close(self) -> None:
        if self._owned:
            self._client.close()

    def __enter__(self) -> "SyncCore":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    def _request(self, method: str, url: str, params: Any = None, json: Any = None) -> Any:
        resp = self._client.request(method, url, params=params, json=json, headers=self._headers)
        if resp.status_code >= 400:
            raise GaianAPIError.from_response(resp)
        return resp.json()

    def user_get(self, path: str, params: Any = None) -> Any:
        return self._request("GET", self.user_base_url + path, params=params)

    def user_post(self, path: str, json: Any = None) -> Any:
        return self._request("POST", self.user_base_url + path, json=json)

    def payment_get(self, path: str, params: Any = None) -> Any:
        return self._request("GET", self.payment_base_url + path, params=params)

    def payment_post(self, path: str, json: Any = None) -> Any:
        return self._request("POST", self.payment_base_url + path, json=json)


class AsyncCore:
    def __init__(
        self,
        api_key: str,
        user_base_url: str,
        payment_base_url: str,
        client: Optional[httpx.AsyncClient] = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self.user_base_url = user_base_url
        self.payment_base_url = payment_base_url
        self._headers = {"x-api-key": api_key}
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._owned = client is None

    async def aclose(self) -> None:
        if self._owned:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncCore":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    async def _request(self, method: str, url: str, params: Any = None, json: Any = None) -> Any:
        resp = await self._client.request(
            method, url, params=params, json=json, headers=self._headers
        )
        if resp.status_code >= 400:
            raise GaianAPIError.from_response(resp)
        return resp.json()

    async def user_get(self, path: str, params: Any = None) -> Any:
        return await self._request("GET", self.user_base_url + path, params=params)

    async def user_post(self, path: str, json: Any = None) -> Any:
        return await self._request("POST", self.user_base_url + path, json=json)

    async def payment_get(self, path: str, params: Any = None) -> Any:
        return await self._request("GET", self.payment_base_url + path, params=params)

    async def payment_post(self, path: str, json: Any = None) -> Any:
        return await self._request("POST", self.payment_base_url + path, json=json)
