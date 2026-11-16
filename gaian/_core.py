from __future__ import annotations

import base64
import hashlib
import hmac
import inspect
import json
import logging
import math
import time
import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any, Concatenate, Generic, ParamSpec, Self, TypeVar
from urllib.parse import quote, urlencode

import httpx
from pydantic import BaseModel, ValidationError

from ._errors import (
    GaianAPIError,
    GaianConnectionError,
    GaianInvalidResponseError,
    GaianTimeoutError,
)

VERSION = "2.0.0"
"""Version of this SDK, sent in the User-Agent header."""

SANDBOX_BASE_URL = "https://sandbox.gaian.network"
"""Gateway of the sandbox environment. No real money moves."""

PRODUCTION_BASE_URL = "https://api.gaian.network"
"""Gateway of the production environment. Real transactions."""

DEFAULT_TIMEOUT = 30.0
"""Default request timeout in seconds."""

_USER_AGENT = f"gaian-python-sdk/{VERSION}"
_API_PREFIX = "/api/v2"
_HTML_ESCAPES = str.maketrans(
    {
        "<": "\\u003c",
        ">": "\\u003e",
        "&": "\\u0026",
        " ": "\\u2028",
        " ": "\\u2029",
    }
)

T = TypeVar("T", bound=BaseModel)
P = ParamSpec("P")


class Environment(StrEnum):
    """Selects the gateway the client talks to. Defaults to SANDBOX."""

    SANDBOX = "sandbox"
    PRODUCTION = "production"


_BASE_URLS = {
    Environment.SANDBOX: SANDBOX_BASE_URL,
    Environment.PRODUCTION: PRODUCTION_BASE_URL,
}


def _number(value: float) -> str:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("gaian: NaN and Infinity cannot be sent as JSON")
    if number != 0 and (abs(number) < 1e-6 or abs(number) >= 1e21):
        mantissa, _, exponent = repr(number).partition("e")
        mantissa = mantissa.removesuffix(".0")
        return f"{mantissa}e{'-' if exponent.startswith('-') else '+'}{abs(int(exponent))}"
    text = format(Decimal(repr(number)), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def canonical_json(value: Any) -> str:
    """Encodes a JSON value exactly as the gateway re-encodes it before checking a signature.

    Keys are sorted at every depth, the output is compact, non-ASCII text is kept as is,
    ``< > &`` and U+2028/U+2029 become ``\\uXXXX``, and a whole number is written without ``.0``.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False).translate(_HTML_ESCAPES)
    if isinstance(value, (int, float)):
        return _number(value)
    if isinstance(value, Mapping):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("gaian: JSON object keys must be strings")
        members = (canonical_json(key) + ":" + canonical_json(value[key]) for key in sorted(value))
        return "{" + ",".join(members) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(canonical_json(item) for item in value) + "]"
    raise TypeError(f"gaian: {type(value).__name__} cannot be sent as JSON")


def canonical_body(body: Any) -> str:
    """Returns the body string that is both signed and sent. Empty for no body and for ``{}``."""
    if body is None:
        return ""
    text = canonical_json(body)
    return "" if text == "{}" else text


def encode_query(params: Mapping[str, Any] | None) -> str:
    """Builds the query string, sorted by key. None and empty-string values are left out."""
    if not params:
        return ""
    pairs: list[tuple[str, str]] = []
    for key in sorted(params):
        value = params[key]
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            value = "true" if value else "false"
        pairs.append((key, str(value)))
    return urlencode(pairs)


def _signature(
    api_key: str, secret_key: str, method: str, path: str, query: str, body: str, timestamp: str
) -> str:
    message = api_key + method.upper() + path.replace(":", "") + query + body + timestamp
    digest = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")


def sign_request(
    *,
    api_key: str,
    secret_key: str,
    method: str,
    path: str,
    query: str,
    body: Any,
    timestamp: str,
) -> str:
    """Computes the ``X-Gaian-Signature`` value of one request.

    ``path`` is the percent-decoded path, ``query`` is the query string exactly as sent
    (without ``?``), ``body`` is the JSON value (None for no body) and ``timestamp`` is unix
    seconds. The secret is used as raw UTF-8 text; the result is base64url with padding.
    """
    return _signature(api_key, secret_key, method, path, query, canonical_body(body), timestamp)


@dataclass(frozen=True)
class Call(Generic[T]):
    """One API call, built by an endpoint function and sent by a client.

    ``segments`` are the unescaped path segments after ``/api/v2``.
    """

    method: str
    segments: tuple[str, ...]
    response: type[T]
    query: Mapping[str, Any] | None = None
    body: Mapping[str, Any] | None = None


def required(name: str, value: str) -> str:
    """Returns a path parameter, or raises ValueError before any request when it is empty."""
    if not value:
        raise ValueError(f"gaian: {name} is required")
    return value


def without_empty(**fields: Any) -> dict[str, Any]:
    """Returns the optional fields that are set. None and ``""`` count as not set; 0 and False stay."""
    return {key: value for key, value in fields.items() if value is not None and value != ""}


@dataclass(frozen=True)
class _Prepared:
    method: str
    path: str
    url: str
    headers: dict[str, str]
    content: bytes | None


class _Gateway:
    def __init__(
        self,
        *,
        api_key: str,
        secret_key: str,
        environment: Environment | str,
        base_url: str | None,
        debug: bool,
        logger: logging.Logger | None,
    ) -> None:
        if not api_key:
            raise ValueError("gaian: api_key is required")
        if not secret_key:
            raise ValueError("gaian: secret_key is required")
        self._api_key = api_key
        self._secret_key = secret_key
        self._base_url = (base_url or _BASE_URLS[Environment(environment)]).rstrip("/")
        self._debug = debug
        self._logger = logger or logging.getLogger("gaian")

    def _prepare(self, call: Call[Any]) -> _Prepared:
        method = call.method.upper()
        path = "/".join((_API_PREFIX, *call.segments))
        escaped = "/".join((_API_PREFIX, *(quote(s, safe="") for s in call.segments)))
        query = encode_query(call.query)
        body = "" if method == "GET" else canonical_body(call.body)
        timestamp = str(int(time.time()))
        headers = {
            "Content-Type": "application/json",
            "User-Agent": _USER_AGENT,
            "X-Gaian-Key": self._api_key,
            "X-Gaian-Signature": _signature(
                self._api_key, self._secret_key, method, path, query, body, timestamp
            ),
            "X-Gaian-Timestamp": timestamp,
            "X-Request-ID": str(uuid.uuid4()),
        }
        url = self._base_url + escaped + ("?" + query if query else "")
        if self._debug:
            self._logger.debug("gaian request %s %s", method, path)
        # The bytes sent are the exact string that was signed: do not re-encode the body.
        return _Prepared(method, path, url, headers, body.encode() if body else None)

    def _transport_error(self, prepared: _Prepared, exc: httpx.HTTPError) -> GaianConnectionError:
        where = f"gaian: {prepared.method} {prepared.path}"
        if isinstance(exc, httpx.TimeoutException):
            return GaianTimeoutError(f"{where}: request timed out")
        return GaianConnectionError(f"{where}: {type(exc).__name__}: {exc}")

    def _finish(self, call: Call[T], prepared: _Prepared, response: httpx.Response) -> T:
        status = response.status_code
        text = response.text
        if self._debug:
            self._logger.debug(
                "gaian response %s %s status=%d", prepared.method, prepared.path, status
            )
        if status >= 400:
            raise GaianAPIError.from_response(status, text, response.headers)
        try:
            return call.response.model_validate(json.loads(text))
        except ValidationError as exc:
            fields = sorted({".".join(str(p) for p in e["loc"]) for e in exc.errors()})
            reason = "unexpected fields: " + ", ".join(fields)
        except ValueError:
            reason = "body is not JSON"
        # Raised outside the except block so the response values pydantic quotes are not chained.
        raise GaianInvalidResponseError(
            status,
            f"{prepared.method} {prepared.path}: {reason}",
            request_id=response.headers.get("x-request-id") or None,
            body=text,
        )


class SyncGateway(_Gateway):
    """Signs and sends calls over a blocking ``httpx.Client``."""

    def __init__(
        self,
        *,
        api_key: str,
        secret_key: str,
        environment: Environment | str = Environment.SANDBOX,
        base_url: str | None = None,
        http_client: httpx.Client | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        debug: bool = False,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            environment=environment,
            base_url=base_url,
            debug=debug,
            logger=logger,
        )
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        """Closes the HTTP client, unless it was passed in as ``http_client``."""
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _execute(self, call: Call[T]) -> T:
        prepared = self._prepare(call)
        try:
            response = self._http.request(
                prepared.method, prepared.url, content=prepared.content, headers=prepared.headers
            )
        except httpx.HTTPError as exc:
            raise self._transport_error(prepared, exc) from exc
        return self._finish(call, prepared, response)


class AsyncGateway(_Gateway):
    """Signs and sends calls over an ``httpx.AsyncClient``."""

    def __init__(
        self,
        *,
        api_key: str,
        secret_key: str,
        environment: Environment | str = Environment.SANDBOX,
        base_url: str | None = None,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        debug: bool = False,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            environment=environment,
            base_url=base_url,
            debug=debug,
            logger=logger,
        )
        self._owns_http = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        """Closes the HTTP client, unless it was passed in as ``http_client``."""
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def _execute(self, call: Call[T]) -> T:
        prepared = self._prepare(call)
        try:
            response = await self._http.request(
                prepared.method, prepared.url, content=prepared.content, headers=prepared.headers
            )
        except httpx.HTTPError as exc:
            raise self._transport_error(prepared, exc) from exc
        return self._finish(call, prepared, response)


def _describe(method: Callable[..., Any], build: Callable[..., Any]) -> None:
    signature = inspect.signature(build)
    owner = inspect.Parameter("self", inspect.Parameter.POSITIONAL_ONLY)
    method.__name__ = build.__name__
    method.__qualname__ = build.__name__
    method.__doc__ = build.__doc__
    method.__signature__ = signature.replace(  # type: ignore[attr-defined]
        parameters=[owner, *signature.parameters.values()],
        return_annotation=inspect.Signature.empty,
    )


def sync_endpoint(build: Callable[P, Call[T]]) -> Callable[Concatenate[SyncGateway, P], T]:
    """Turns an endpoint function into a blocking client method with the same parameters."""

    def method(self: SyncGateway, /, *args: P.args, **kwargs: P.kwargs) -> T:
        return self._execute(build(*args, **kwargs))

    _describe(method, build)
    return method


def async_endpoint(
    build: Callable[P, Call[T]],
) -> Callable[Concatenate[AsyncGateway, P], Awaitable[T]]:
    """Turns an endpoint function into a coroutine client method with the same parameters."""

    async def method(self: AsyncGateway, /, *args: P.args, **kwargs: P.kwargs) -> T:
        return await self._execute(build(*args, **kwargs))

    _describe(method, build)
    return method
