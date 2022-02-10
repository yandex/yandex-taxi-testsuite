from testsuite._internal import fixture_types
from testsuite.daemons import service_client


async def test_handler(
        mockserver: fixture_types.MockserverFixture,
        mockserver_client: service_client.Client,
):
    @mockserver.handler('/test')
    def _test(request: fixture_types.MockserverRequest):
        return mockserver.make_response('test', 200)

    response = await mockserver_client.get('test')
    assert response.status_code == 200
    assert response.content == b'test'


async def test_json_handler(
        mockserver: fixture_types.MockserverFixture,
        mockserver_client: service_client.Client,
):
    @mockserver.json_handler('/test')
    def _test(request: fixture_types.MockserverRequest):
        assert request.json == {'cmd': 'ping'}
        return {'msg': 'pong'}

    response = await mockserver_client.post('test', json={'cmd': 'ping'})
    assert response.status_code == 200
    assert response.json() == {'msg': 'pong'}


async def test_handler_callqueue(
        mockserver: fixture_types.MockserverFixture,
        mockserver_client: service_client.Client,
):
    @mockserver.json_handler('/test')
    def test(request: fixture_types.MockserverRequest):
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


async def test_handler_callqueue_wait(
        mockserver: fixture_types.MockserverFixture,
        mockserver_client: service_client.Client,
):
    @mockserver.json_handler('/test')
    def test(request: fixture_types.MockserverRequest):
        assert request.json == {'cmd': 'ping'}
        return {'msg': 'pong'}

    assert not test.has_calls
    response = await mockserver_client.post('test', json={'cmd': 'ping'})
    assert response.status_code == 200

    call = await test.wait_call()
    assert call['request'].path == '/test'


async def test_prefix_handler(
        mockserver: fixture_types.MockserverFixture,
        mockserver_client: service_client.Client,
):
    @mockserver.json_handler('/test', prefix=True)
    def test(request: fixture_types.MockserverRequest):
        return {'msg': 'pong'}

    response = await mockserver_client.get('test')
    assert response.status_code == 200
    assert test.next_call()

    response = await mockserver_client.get('test123')
    assert response.status_code == 200
    assert test.next_call()
