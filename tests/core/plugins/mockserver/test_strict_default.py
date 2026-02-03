import aiohttp
import pytest

import testsuite

from .client import Client


@pytest.fixture
async def mockserver_client(mockserver: testsuite.MockserverFixture):
    async with aiohttp.ClientSession() as session:
        yield Client(base_url=mockserver.base_url, session=session)


@pytest.fixture
def mockserver_strict_default():
    return True


@pytest.mark.mockserver_assert_lost_calls
async def test_lost_some_calls(
    mockserver: testsuite.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/test')
    def mock(request):
        pass

    response = await mockserver_client.get('test')
    assert response.status == 200
