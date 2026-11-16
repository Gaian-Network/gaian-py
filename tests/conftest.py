import inspect
import json
from typing import Any

import pytest

import gaian

BASE = "https://gw.test"
API_KEY = "test-api-key"
SECRET = "test-secret-key"


class Harness:
    """Runs the same call against the sync or the async client."""

    def __init__(self, flavor: str, **opts: Any) -> None:
        opts.setdefault("base_url", BASE)
        cls = gaian.AsyncGaianClient if flavor == "async" else gaian.GaianClient
        self.flavor = flavor
        self.client = cls(api_key=API_KEY, secret_key=SECRET, **opts)

    async def call(self, name: str, **kwargs: Any) -> Any:
        result = getattr(self.client, name)(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def close(self) -> None:
        if self.flavor == "async":
            await self.client.aclose()
        else:
            self.client.close()


@pytest.fixture(params=["sync", "async"])
async def make_harness(request):
    made: list[Harness] = []

    def factory(**opts: Any) -> Harness:
        h = Harness(request.param, **opts)
        made.append(h)
        return h

    yield factory
    for h in made:
        await h.close()


@pytest.fixture
def gw(make_harness):
    return make_harness()


def sent(httpx_mock, n: int = 0):
    return httpx_mock.get_requests()[n]


def body_of(req) -> Any:
    return json.loads(req.content)


def query_of(req) -> dict:
    return dict(req.url.params)
