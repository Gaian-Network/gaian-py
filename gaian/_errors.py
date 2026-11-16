from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


class GaianError(Exception):
    """Base class of every error raised by this SDK."""


class GaianAPIError(GaianError):
    """Raised for every response with an HTTP status of 400 or above.

    ``code`` is derived from the HTTP status (``NOT_FOUND``, ``CONFLICT``, ...).
    ``api_code`` is the code set by the service itself (payment endpoints only,
    for example ``IDENTITY_REQUIRED``). ``body`` is the raw response body, kept
    as received even when it is not JSON. Quote ``request_id`` to Gaian support.
    """

    def __init__(
        self,
        status_code: int,
        message: str = "",
        *,
        api_code: str | None = None,
        request_id: str | None = None,
        body: str = "",
    ) -> None:
        self.status_code = status_code
        self.code = _status_to_code(status_code)
        self.api_code = api_code
        self.message = message or f"HTTP {status_code}"
        self.request_id = request_id
        self.body = body
        super().__init__(self._describe())

    def _describe(self) -> str:
        parts = [f"gaian: api error: status={self.status_code}", f"code={self.code}"]
        if self.api_code:
            parts.append(f"api_code={self.api_code}")
        parts.append(f"message={self.message}")
        if self.request_id:
            parts.append(f"request_id={self.request_id}")
        return " ".join(parts)

    @classmethod
    def from_response(
        cls, status_code: int, body: str, headers: Mapping[str, str]
    ) -> GaianAPIError:
        """Builds the error from a raw response. Never fails on an empty or non-JSON body."""
        message = ""
        api_code: str | None = None
        request_id: str | None = None

        parsed = _parse_object(body)
        if parsed is not None:
            request_id = _text(parsed.get("requestId"))
            api_code = _text(parsed.get("code"))
            message = _text(parsed.get("message")) or ""
            nested = parsed.get("error")
            if isinstance(nested, dict):
                api_code = _text(nested.get("code")) or api_code
                message = message or _text(nested.get("message")) or ""
            elif isinstance(nested, str):
                message = message or nested

        return cls(
            status_code,
            message,
            api_code=api_code,
            request_id=request_id or headers.get("x-request-id") or None,
            body=body,
        )


class GaianConnectionError(GaianError):
    """Raised when the request never got a response (DNS, refused connection, TLS, ...).

    The original ``httpx`` exception is available as ``__cause__``.
    """


class GaianTimeoutError(GaianConnectionError):
    """Raised when the request timed out. The request may still have reached the API."""


class GaianInvalidResponseError(GaianError):
    """Raised when a 2xx response has a body the SDK cannot decode.

    The request was accepted by the API: do not blindly retry a call that moves money.
    """

    def __init__(self, status_code: int, reason: str, *, request_id: str | None, body: str) -> None:
        self.status_code = status_code
        self.request_id = request_id
        self.body = body
        text = f"gaian: invalid response: status={status_code} reason={reason}"
        if request_id:
            text += f" request_id={request_id}"
        super().__init__(text)


class WebhookVerificationError(GaianError):
    """Raised by ``verify_webhook`` for a wrong signature or a timestamp outside the tolerance."""


def _parse_object(body: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(body)
    except ValueError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    402: "PAYMENT_REQUIRED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "UNPROCESSABLE_ENTITY",
    429: "RATE_LIMITED",
}


def _status_to_code(status_code: int) -> str:
    if status_code >= 500:
        return "SERVER_ERROR"
    return _STATUS_CODES.get(status_code, "UNKNOWN")


def _has_status(err: BaseException | None, status_code: int) -> bool:
    seen: set[int] = set()
    while err is not None and id(err) not in seen:
        if isinstance(err, GaianAPIError):
            return err.status_code == status_code
        seen.add(id(err))
        err = err.__cause__ or err.__context__
    return False


def is_not_found(err: BaseException) -> bool:
    """Reports whether err is, or was raised from, a GaianAPIError with status 404."""
    return _has_status(err, 404)


def is_conflict(err: BaseException) -> bool:
    """Reports whether err is, or was raised from, a GaianAPIError with status 409."""
    return _has_status(err, 409)


def is_unauthorized(err: BaseException) -> bool:
    """Reports whether err is, or was raised from, a GaianAPIError with status 401."""
    return _has_status(err, 401)


def is_forbidden(err: BaseException) -> bool:
    """Reports whether err is, or was raised from, a GaianAPIError with status 403."""
    return _has_status(err, 403)


def is_rate_limited(err: BaseException) -> bool:
    """Reports whether err is, or was raised from, a GaianAPIError with status 429."""
    return _has_status(err, 429)
