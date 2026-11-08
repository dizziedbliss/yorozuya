import pytest

from sources.fx import FxSource
from tests.helpers import fake_client, fixture

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def test_rates_are_turned_into_rupees_per_unit_for_next_run():
    client = fake_client({"api.frankfurter.dev/v1/latest": fixture("frankfurter")})

    result = await FxSource().fetch(client, {})

    assert result.jobs == []
    assert result.state == {"USD": 93.91, "EUR": 104.86, "GBP": 125.71}
