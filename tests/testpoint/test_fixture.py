import pytest

from testsuite._internal import fixture_types


@pytest.mark.parametrize('data', [None, 'hello', {'msg': 'hello'}])
async def test_basic(
        mockserver_client, testpoint: fixture_types.TestpointFixture, data,
):
    @testpoint('ping')
    def ping(data):
        return data

    response = await mockserver_client.post(
        'testpoint', json={'name': 'ping', 'data': data},
    )
    assert response.status_code == 200
    assert response.json() == {'data': data}
    assert ping.next_call() == {'data': data}


async def test_basic_async(
        mockserver_client, testpoint: fixture_types.TestpointFixture,
):
    @testpoint('ping')
    async def ping(data):
        return data

    response = await mockserver_client.post(
        'testpoint', json={'name': 'ping', 'data': 'test'},
    )
    assert response.status_code == 200
    assert response.json() == {'data': 'test'}
    assert ping.next_call() == {'data': 'test'}


async def test_next_call(
        mockserver_client, testpoint: fixture_types.TestpointFixture,
):
    @testpoint('foo')
    def foo_point(data):
        pass

    response = await mockserver_client.post(
        'testpoint', json={'name': 'foo', 'data': 'test'},
    )
    assert response.status_code == 200

    assert foo_point.has_calls
    assert foo_point.next_call() == {'data': 'test'}


async def test_wait_call(
        mockserver_client, testpoint: fixture_types.TestpointFixture,
):
    @testpoint('foo')
    def foo_point(data):
        return 'foo'

    response = await mockserver_client.post(
        'testpoint', json={'name': 'foo', 'data': 'test'},
    )
    assert response.status_code == 200
    assert await foo_point.wait_call() == {'data': 'test'}
