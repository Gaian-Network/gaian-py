from __future__ import annotations

import httpx


class GaianAPIError(Exception):
    """Raised when the Gaian API returns a 4xx or 5xx response."""

    def __init__(self, status_code: int, error: str = "", message: str = "") -> None:
        self.status_code = status_code
        self.error = error
        self.message = message or error
        super().__init__(f"gaian: api error {status_code}: {self.message}")

    @classmethod
    def from_response(cls, resp: httpx.Response) -> "GaianAPIError":
        try:
            body = resp.json()
            return cls(
                status_code=resp.status_code,
                error=body.get("error", ""),
                message=body.get("message", resp.text),
            )
        except Exception:
            return cls(status_code=resp.status_code, message=resp.text)


def is_not_found(err: Exception) -> bool:
    return isinstance(err, GaianAPIError) and err.status_code == 404


def is_conflict(err: Exception) -> bool:
    return isinstance(err, GaianAPIError) and err.status_code == 409


def is_unauthorized(err: Exception) -> bool:
    return isinstance(err, GaianAPIError) and err.status_code == 401


def is_forbidden(err: Exception) -> bool:
    return isinstance(err, GaianAPIError) and err.status_code == 403
