import aiohttp.web

from testsuite._internal import fixture_types
from testsuite.utils import http


async def test_basic(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.json_handler('/arbitrary/path')
    def handler(
            *, body_json, content_type, cookies, headers, method, path, query,
    ):
        assert body_json == {'k': 'v'}
        assert content_type == 'application/json'
        assert headers['foo'] == 'bar'
        assert path == '/arbitrary/path'
        assert method == 'POST'
        assert cookies == {'c1': 'c2'}
        assert query == {'foo': 'bar'}
        return {}

    client = create_service_client(mockserver.base_url)
    response = await client.post(
        'arbitrary/path',
        json={'k': 'v'},
        headers={'foo': 'bar'},
        cookies={'c1': 'c2'},
        params={'foo': 'bar'},
    )
    assert response.status_code == 200
    assert handler.times_called == 1


async def test_body_binary(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.json_handler('/arbitrary/path')
    def handler(*, body_binary):
        assert body_binary == b'Hello, world!'

    client = create_service_client(mockserver.base_url)
    response = await client.post('arbitrary/path', data='Hello, world!')
    assert response.status_code == 200
    assert handler.times_called == 1


async def test_form(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.json_handler('/arbitrary/path')
    def handler(*, form):
        assert form == {'key1': 'val1', 'key2': 'val2'}

    client = create_service_client(mockserver.base_url)
    response = await client.post(
        'arbitrary/path',
        headers={'content-type': 'application/x-www-form-urlencoded'},
        data='key1=val1&key2=val2',
    )
    assert response.status_code == 200
    assert handler.times_called == 1


async def test_request_type(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.json_handler('/arbitrary/path')
    def handler(request: aiohttp.web.BaseRequest):
        assert isinstance(request, aiohttp.web.BaseRequest)

    client = create_service_client(mockserver.base_url)
    response = await client.post('arbitrary/path')
    assert response.status_code == 200
    assert handler.times_called == 1


async def test_naorgs(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.json_handler('/arbitrary/path')
    def handler():
        pass

    client = create_service_client(mockserver.base_url)
    response = await client.post('arbitrary/path')
    assert response.status_code == 200
    assert handler.times_called == 1


async def test_star_args(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.json_handler('/arbitrary/path')
    def handler(*args, **kwargs):
        assert len(args) == 1
        assert isinstance(args[0], http.Request)

    client = create_service_client(mockserver.base_url)
    response = await client.post('arbitrary/path')
    assert response.status_code == 200
    assert handler.times_called == 1
