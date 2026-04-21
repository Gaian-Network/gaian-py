import pytest
import gaian


SANDBOX_USER = "https://dev-user.gaian-dev.network"
SANDBOX_PMT = "https://dev-payments.gaian-dev.network"


@pytest.fixture
def client():
    with gaian.GaianClient(
        api_key="test-key",
        env=gaian.Environment.SANDBOX,
    ) as c:
        yield c


@pytest.fixture
async def async_client():
    async with gaian.AsyncGaianClient(
        api_key="test-key",
        env=gaian.Environment.SANDBOX,
    ) as c:
        yield c
