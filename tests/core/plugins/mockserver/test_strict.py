import asyncio

import aiohttp
import pytest

from testsuite._internal import fixture_types


# TODO: move to conftest.py?
class Client:
    def __init__(self, *, base_url, session):
        self._session = session
        self._base_url = base_url

    def get(self, path, **kwargs):
        return self._request('GET', path, **kwargs)

    def _request(self, method, path, **kwargs):
        url = self._base_url + path
        return self._session.request(method, url, **kwargs)


@pytest.fixture
async def mockserver_client(mockserver: fixture_types.MockserverFixture):
    async with aiohttp.ClientSession() as session:
        yield Client(base_url=mockserver.base_url, session=session)


async def test_checked(
    mockserver: fixture_types.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/test', strict=True)
    def mock(request):
        pass

    response = await mockserver_client.get('test')
    assert response.status == 200

    mock_request = mock.next_call()
    assert mock_request['request']

    # Note: no assert in mockserver's teardown


@pytest.mark.mockserver_assert_lost_calls
async def test_lost_single_call(
    mockserver: fixture_types.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/test', strict=True)
    def mock(request):
        pass

    response = await mockserver_client.get('test')
    assert response.status == 200


@pytest.mark.mockserver_assert_lost_calls
async def test_lost_some_calls(
    mockserver: fixture_types.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/test', strict=True)
    def mock(request):
        pass

    response = await mockserver_client.get('test')
    assert response.status == 200
    response = await mockserver_client.get('test')
    assert response.status == 200

    mock_request = mock.next_call()
    assert mock_request['request']
