from testsuite._internal import fixture_types


def test_schema_is_https(mockserver_ssl: fixture_types.MockserverFixture):
    url: str = mockserver_ssl.url('some/path')
    assert url.startswith('https://')


async def test_request_is_handled(
        mockserver_ssl: fixture_types.MockserverFixture, mockserver_ssl_client,
):
    @mockserver_ssl.handler('/test')
    def _handle(request):
        return mockserver_ssl.make_response('test', 200)

    response = await mockserver_ssl_client.get('test')
    assert response.status_code == 200
    assert response.content == b'test'
