"""Recomputes a request signature the way the gateway does, without using the SDK signer."""

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote

_HTML_ESCAPES = {"<": "\\u003c", ">": "\\u003e", "&": "\\u0026", " ": "\\u2028", " ": "\\u2029"}


def go_marshal(value: Any) -> str:
    if isinstance(value, dict):
        items = (go_marshal(k) + ":" + go_marshal(value[k]) for k in sorted(value))
        return "{" + ",".join(items) + "}"
    if isinstance(value, list):
        return "[" + ",".join(go_marshal(v) for v in value) + "]"
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e21:
        return str(int(value))
    text = json.dumps(value, ensure_ascii=False)
    return "".join(_HTML_ESCAPES.get(c, c) for c in text)


def gateway_body(raw: bytes) -> str:
    if raw in (b"", b"{}"):
        return ""
    return go_marshal(json.loads(raw))


@dataclass
class GatewayCheck:
    ok: bool
    signed_path: str
    signed_body: str
    request_id: str
    timestamp: str
    expected: str
    received: str


def gateway_verify(request, api_key: str, secret: str) -> GatewayCheck:
    raw_path, _, raw_query = request.url.raw_path.decode("ascii").partition("?")
    signed_path = unquote(raw_path).replace(":", "")
    signed_body = gateway_body(request.content)
    timestamp = request.headers.get("x-gaian-timestamp", "")
    message = api_key + request.method.upper() + signed_path + raw_query + signed_body + timestamp
    digest = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    expected = base64.urlsafe_b64encode(digest).decode()
    received = request.headers.get("x-gaian-signature", "")
    return GatewayCheck(
        ok=expected == received and request.headers.get("x-gaian-key") == api_key,
        signed_path=signed_path,
        signed_body=signed_body,
        request_id=request.headers.get("x-request-id", ""),
        timestamp=timestamp,
        expected=expected,
        received=received,
    )
