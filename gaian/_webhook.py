from __future__ import annotations

import hashlib
import hmac
import math
import time

from ._errors import WebhookVerificationError

DEFAULT_WEBHOOK_TOLERANCE_SECONDS = 300
"""Default maximum distance, in seconds, between a webhook timestamp and the local clock."""


def verify_webhook(
    *,
    secret: str,
    signature: str,
    timestamp: str,
    body: bytes,
    tolerance_seconds: float = DEFAULT_WEBHOOK_TOLERANCE_SECONDS,
) -> None:
    """Verifies that a webhook delivery was signed by Gaian with the endpoint's secret.

    ``signature`` is the ``X-Gaian-Signature`` header (``sha256=<hex>``), ``timestamp`` the
    ``X-Gaian-Timestamp`` header (unix seconds) and ``body`` the request body exactly as
    received, before any JSON parsing. Returns nothing on success. Raises
    WebhookVerificationError for a wrong signature or a timestamp more than
    ``tolerance_seconds`` in the past or the future, and TypeError when ``body`` is not bytes.
    A ``tolerance_seconds`` that is zero, negative, NaN, infinite or not a number falls back
    to DEFAULT_WEBHOOK_TOLERANCE_SECONDS, so the timestamp check cannot be switched off.
    """
    if not isinstance(body, (bytes, bytearray, memoryview)):
        raise TypeError("gaian: verify_webhook needs the raw request body as bytes")
    if not secret:
        raise WebhookVerificationError("gaian: webhook verification failed: secret is required")
    if not (isinstance(timestamp, str) and timestamp.isascii() and timestamp.isdigit()):
        raise WebhookVerificationError(
            "gaian: webhook verification failed: timestamp is not unix seconds"
        )

    mac = hmac.new(secret.encode(), timestamp.encode() + b".", hashlib.sha256)
    mac.update(body)
    expected = ("sha256=" + mac.hexdigest()).encode()
    received = signature.encode() if isinstance(signature, str) else b""
    if not hmac.compare_digest(received, expected):
        raise WebhookVerificationError("gaian: webhook verification failed: signature mismatch")

    tolerance: float = DEFAULT_WEBHOOK_TOLERANCE_SECONDS
    if (
        isinstance(tolerance_seconds, (int, float))
        and math.isfinite(tolerance_seconds)
        and tolerance_seconds > 0
    ):
        tolerance = tolerance_seconds
    if abs(int(time.time()) - int(timestamp)) > tolerance:
        raise WebhookVerificationError(
            "gaian: webhook verification failed: timestamp outside tolerance"
        )
