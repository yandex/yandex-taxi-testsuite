async def test_handler(mockserver, mockserver_client):
    @mockserver.handler('/test')
    def _test(request):
        return mockserver.make_response('test', 200)

    response = await mockserver_client.get('test')
    assert response.status_code == 200
    assert response.content == b'test'


async def test_json_handler(mockserver, mockserver_client):
    @mockserver.json_handler('/test')
    def _test(request):
        assert request.json == {'cmd': 'ping'}
        return {'msg': 'pong'}

    response = await mockserver_client.post('test', json={'cmd': 'ping'})
    assert response.status_code == 200
    assert response.json() == {'msg': 'pong'}


async def test_handler_callqueue(mockserver, mockserver_client):
    @mockserver.json_handler('/test')
    def test(request):
        assert request.json == {'cmd': 'ping'}
        return {'msg': 'pong'}

    assert not test.has_calls
    assert test.times_called == 0
    response = await mockserver_client.post('test', json={'cmd': 'ping'})
    assert response.status_code == 200

    assert test.has_calls
    assert test.times_called == 1
    call = test.next_call()
    assert call['request'].path == '/test'


async def test_handler_callqueue_wait(mockserver, mockserver_client):
    @mockserver.json_handler('/test')
    def test(request):
        assert request.json == {'cmd': 'ping'}
        return {'msg': 'pong'}

    assert not test.has_calls
    response = await mockserver_client.post('test', json={'cmd': 'ping'})
    assert response.status_code == 200

    call = await test.wait_call()
    assert call['request'].path == '/test'


async def test_prefix_handler(mockserver, mockserver_client):
    @mockserver.json_handler('/test', prefix=True)
    def test(request):
        return {'msg': 'pong'}

    response = await mockserver_client.get('test')
    assert response.status_code == 200
    assert test.next_call()

    response = await mockserver_client.get('test123')
    assert response.status_code == 200
    assert test.next_call()
