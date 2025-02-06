# pylint: disable=protected-access
import aiohttp
import aiohttp.web
import pytest

from testsuite.mockserver import exceptions
from testsuite._internal import fixture_types


class UserError(Exception):
    pass


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
    mockserver: fixture_types.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    def _foo_handler(request):
        return {'msg': 'hello'}

    response = await mockserver_client.get('/foo')
    assert response.status == 200
    data = await response.json()

    assert data == {'msg': 'hello'}


async def test_async_json_handler(
    mockserver: fixture_types.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    async def _foo_handler(request):
        return {'msg': 'hello'}

    response = await mockserver_client.get('/foo')
    assert response.status == 200
    data = await response.json()

    assert data == {'msg': 'hello'}


async def test_handler(
    mockserver: fixture_types.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    def _foo_handler(request):
        return mockserver.make_response('hello')

    response = await mockserver_client.get('/foo')
    assert response.status == 200
    data = await response.content.read()

    assert data == b'hello'


async def test_user_error(
    mockserver: fixture_types.MockserverFixture,
    mockserver_client: Client,
    mockserver_errors_list,
    mockserver_errors_pop,
):
    @mockserver.json_handler('/foo')
    def _foo_handler(request):
        raise UserError

    response = await mockserver_client.get('/foo')
    assert response.status == 500

    assert len(mockserver_errors_list) == 1

    error = mockserver_errors_pop()
    assert isinstance(error, UserError)


async def test_nohandler(
    mockserver: fixture_types.MockserverFixture,
    mockserver_client: Client,
    mockserver_errors_list,
    mockserver_errors_pop,
):
    response = await mockserver_client.get(
        '/foo123',
        headers={mockserver.trace_id_header: mockserver.trace_id},
    )
    assert response.status == 500

    assert len(mockserver_errors_list) == 1

    error = mockserver_errors_pop()
    assert isinstance(error, exceptions.HandlerNotFoundError)


async def test_aiohttp_response(
    mockserver: fixture_types.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    def _foo_handler(request):
        return aiohttp.web.json_response({'foo': 'bar'})

    response = await mockserver_client.get('/foo')

    assert response.status == 200
    assert await response.json() == {'foo': 'bar'}
