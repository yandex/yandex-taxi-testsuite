import inspect

import aiohttp.web

from testsuite._internal import fixture_types
from testsuite.utils import http


async def test_request_wrapper_attributes(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.handler('/arbitrary/path', prefix=True)
    def _handler(request: http.Request):
        assert request.method == 'POST'
        assert request.url == mockserver.base_url + 'arbitrary/path?k=v'
        assert request.path == '/arbitrary/path'
        assert request.query_string == b'k=v'
        assert request.get_data() == b'some data'
        assert len(request.args) == 1
        assert request.args['k'] == 'v'
        assert request.headers['arbitrary-header'] == 'value'

        return mockserver.make_response()

    client = create_service_client(
        mockserver.base_url, headers={'arbitrary-header': 'value'},
    )
    response = await client.post('arbitrary/path?k=v', data=b'some data')
    assert response.status_code == 200


async def test_response_attributes(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.handler('/arbitrary/path')
    def _handler(request: http.Request):
        return mockserver.make_response(
            response='forbidden',
            status=403,
            headers={'arbitrary-header': 'value'},
        )

    client = create_service_client(mockserver.base_url)
    response = await client.post('arbitrary/path')
    assert response.status_code == 403
    assert response.headers['arbitrary-header'] == 'value'
    assert response.text == 'forbidden'


async def test_request_json(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.handler('/arbitrary/path')
    def _handler(request):
        assert request.json == {'k': 'v'}
        return mockserver.make_response()

    client = create_service_client(mockserver.base_url)
    response = await client.post('arbitrary/path', data='{"k": "v"}')
    assert response.status_code == 200


async def test_response_json(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.json_handler('/arbitrary/path')
    def _handler(request: http.Request):
        return {'k': 'v'}

    client = create_service_client(mockserver.base_url)
    response = await client.post('arbitrary/path')
    assert response.status_code == 200
    json_response = response.json()
    assert json_response == {'k': 'v'}


async def test_raw_request_parameter(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.aiohttp_json_handler('/arbitrary/path')
    async def _handler(request: aiohttp.web.Request):
        is_json_method_async = inspect.iscoroutinefunction(request.json)
        # the non-wrapped request has async json method.
        assert is_json_method_async
        return mockserver.make_response()

    client = create_service_client(mockserver.base_url)
    response = await client.post('arbitrary/path')
    assert response.status_code == 200


async def test_request_form(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.json_handler('/arbitrary/path')
    async def _handler(request: http.Request):
        form = request.form
        assert form == {'key1': 'val1', 'key2': 'val2'}
        return mockserver.make_response()

    client = create_service_client(mockserver.base_url)
    response = await client.post(
        'arbitrary/path',
        headers={'content-type': 'application/x-www-form-urlencoded'},
        data='key1=val1&key2=val2',
    )
    assert response.status_code == 200
