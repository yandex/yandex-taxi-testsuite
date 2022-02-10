async def test_proxy(mockserver, mockserver_client):
    @mockserver.json_handler('http://example.org/foo/bar')
    def example_handler(request):
        return {}

    response = await mockserver_client.get(
        '/foo/bar', headers={'Host': 'example.org'},
    )
    assert response.status_code == 200
    assert example_handler.times_called == 1


async def test_prefixed(mockserver, mockserver_client):
    example_mockserver = mockserver.new('http://example.org/')

    @example_mockserver.json_handler('/foo/bar')
    def example_handler(request):
        return {}

    response = await mockserver_client.get(
        '/foo/bar', headers={'Host': 'example.org'},
    )
    assert response.status_code == 200
    assert example_handler.times_called == 1
