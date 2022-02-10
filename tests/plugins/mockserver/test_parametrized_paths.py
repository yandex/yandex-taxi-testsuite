from testsuite._internal import fixture_types
from testsuite.utils import http


async def test_regex_path(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.handler(r'/path/(?P<num>\d+)', regex=True)
    def _handler(request: http.Request, num: str):
        assert request.path == '/path/012'
        assert num == '012'
        return mockserver.make_response()

    @mockserver.handler('/path', prefix=True)
    def _fallback_handler(request: http.Request):
        return mockserver.make_response(status=404)

    client = create_service_client(mockserver.base_url)
    response = await client.post('path/012')
    assert _fallback_handler.times_called == 0
    assert _handler.times_called == 1
    assert response.status_code == 200


async def test_regex_path_not_matched(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.handler(r'/path/(?P<num>\d+)', regex=True)
    def _handler(request: http.Request, num: str):
        return mockserver.make_response()

    @mockserver.handler('/path', prefix=True)
    def _fallback_handler(request: http.Request):
        return mockserver.make_response(status=404)

    client = create_service_client(mockserver.base_url)
    response = await client.post('path/abc')
    assert _handler.times_called == 0
    assert _fallback_handler.times_called == 1
    assert response.status_code == 404


async def test_regex_pathes_are_matched_in_reversed_addition_order(
        mockserver: fixture_types.MockserverFixture, create_service_client,
):
    @mockserver.handler(r'/path/(?P<param_first>[^/]+)', regex=True)
    def _handler_first(request: http.Request, param_first: str):
        return mockserver.make_response()

    @mockserver.handler(r'/path/(?P<param_second>[^/]+)', regex=True)
    def _handler_second(request: http.Request, param_second: str):
        return mockserver.make_response()

    client = create_service_client(mockserver.base_url)
    response = await client.post('path/abc')
    assert _handler_first.times_called == 0
    assert _handler_second.times_called == 1
    assert response.status_code == 200
