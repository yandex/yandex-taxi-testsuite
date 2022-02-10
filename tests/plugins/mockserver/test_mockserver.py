# pylint: disable=protected-access
import aiohttp
import pytest

from testsuite._internal import fixture_types


class Client:
    def __init__(self, *, base_url, session):
        self._session = session
        self._base_url = base_url

    def get(self, path, **kwargs):
        return self._request('GET', path, **kwargs)

    def _request(self, method, path, **kwargs):
        url = _build_url(self._base_url, path)
        return self._session.request(method, url, **kwargs)


def _build_url(base_url, path):
    return '%s/%s' % (base_url.rstrip('/'), path.lstrip('/'))


@pytest.fixture
async def mockserver_client(mockserver: fixture_types.MockserverFixture):
    async with aiohttp.ClientSession() as session:
        yield Client(base_url=mockserver.base_url, session=session)


async def test_json_handler(
        mockserver: fixture_types.MockserverFixture, mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    def _foo_handler(request):
        return {'msg': 'hello'}

    response = await mockserver_client.get('/foo')
    assert response.status == 200
    data = await response.json()

    assert data == {'msg': 'hello'}


async def test_async_json_handler(
        mockserver: fixture_types.MockserverFixture, mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    async def _foo_handler(request):
        return {'msg': 'hello'}

    response = await mockserver_client.get('/foo')
    assert response.status == 200
    data = await response.json()

    assert data == {'msg': 'hello'}


async def test_handler(
        mockserver: fixture_types.MockserverFixture, mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    def _foo_handler(request):
        return mockserver.make_response('hello')

    response = await mockserver_client.get('/foo')
    assert response.status == 200
    data = await response.content.read()

    assert data == b'hello'
