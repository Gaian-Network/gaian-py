import json
import time
from pathlib import Path

import pytest

import gaian

VECTORS = json.loads((Path(__file__).parent / "data" / "signature-vectors.json").read_text("utf-8"))
NOW = int(VECTORS["timestamp"])
FIRST = VECTORS["webhooks"][0]


@pytest.fixture(autouse=True)
def frozen_clock(monkeypatch):
    monkeypatch.setattr(time, "time", lambda: float(NOW))


def verify(**over):
    args = {
        "secret": VECTORS["webhookSecret"],
        "signature": FIRST["signature"],
        "timestamp": FIRST["timestamp"],
        "body": FIRST["body"].encode(),
    }
    return gaian.verify_webhook(**{**args, **over})


@pytest.mark.parametrize("hook", VECTORS["webhooks"], ids=lambda h: h["name"])
def test_verify_webhook_accepts_vector(hook):
    verify(signature=hook["signature"], timestamp=hook["timestamp"], body=hook["body"].encode())


@pytest.mark.parametrize(
    "over",
    [
        {"signature": "sha256=" + "0" * 64},
        {"signature": "sha256=abc"},
        {"signature": FIRST["signature"].removeprefix("sha256=")},
        {"signature": ""},
        {"body": FIRST["body"].replace("150000", "950000").encode()},
        {"secret": "whsec_other"},
        {"timestamp": "abc"},
    ],
    ids=[
        "wrong_signature",
        "short_signature",
        "no_prefix",
        "empty_signature",
        "tampered_body",
        "wrong_secret",
        "bad_timestamp",
    ],
)
def test_verify_webhook_rejects_bad_input(over):
    with pytest.raises(gaian.WebhookVerificationError):
        verify(**over)


@pytest.mark.parametrize("offset", [301, -301])
def test_verify_webhook_rejects_timestamp_more_than_300s_away(monkeypatch, offset):
    monkeypatch.setattr(time, "time", lambda: float(NOW + offset))

    with pytest.raises(gaian.WebhookVerificationError):
        verify()


@pytest.mark.parametrize("offset", [300, -300])
def test_verify_webhook_accepts_timestamp_exactly_300s_away(monkeypatch, offset):
    monkeypatch.setattr(time, "time", lambda: float(NOW + offset))

    verify()


def test_verify_webhook_honours_custom_tolerance(monkeypatch):
    monkeypatch.setattr(time, "time", lambda: float(NOW + 30))

    with pytest.raises(gaian.WebhookVerificationError):
        verify(tolerance_seconds=10)
    verify(tolerance_seconds=60)


@pytest.mark.parametrize(
    "body", [FIRST["body"], json.loads(FIRST["body"])], ids=["str", "parsed_dict"]
)
def test_verify_webhook_takes_raw_bytes_only(body):
    with pytest.raises(TypeError):
        verify(body=body)
