import pytest

from testsuite._internal import fixture_types


@pytest.mark.parametrize('data', [None, 'hello', {'msg': 'hello'}])
async def test_basic(
    mockserver_client,
    testpoint: fixture_types.TestpointFixture,
    data,
):
    @testpoint('ping')
    def ping(data):
        return data

    response = await mockserver_client.post(
        'testpoint',
        json={'name': 'ping', 'data': data},
    )
    assert response.status_code == 200
    assert response.json() == {'data': data, 'handled': True}
    assert ping.next_call() == {'data': data}


async def test_basic_async(
    mockserver_client,
    testpoint: fixture_types.TestpointFixture,
):
    @testpoint('ping')
    async def ping(data):
        return data

    response = await mockserver_client.post(
        'testpoint',
        json={'name': 'ping', 'data': 'test'},
    )
    assert response.status_code == 200
    assert response.json() == {'data': 'test', 'handled': True}
    assert ping.next_call() == {'data': 'test'}


async def test_next_call(
    mockserver_client,
    testpoint: fixture_types.TestpointFixture,
):
    @testpoint('foo')
    def foo_point(data):
        pass

    response = await mockserver_client.post(
        'testpoint',
        json={'name': 'foo', 'data': 'test'},
    )
    assert response.status_code == 200

    assert foo_point.has_calls
    assert foo_point.next_call() == {'data': 'test'}


async def test_wait_call(
    mockserver_client,
    testpoint: fixture_types.TestpointFixture,
):
    @testpoint('foo')
    def foo_point(data):
        return 'foo'

    response = await mockserver_client.post(
        'testpoint',
        json={'name': 'foo', 'data': 'test'},
    )
    assert response.status_code == 200
    assert await foo_point.wait_call() == {'data': 'test'}


async def test_not_handled(
    mockserver_client,
    testpoint: fixture_types.TestpointFixture,
):
    response = await mockserver_client.post(
        'testpoint',
        json={'name': 'ping', 'data': 'data string'},
    )
    assert response.status_code == 200
    assert response.json() == {'data': None, 'handled': False}


def test_deletion_by_name(testpoint):
    @testpoint('foo')
    def foo_point(data): ...

    assert 'foo' in testpoint
    del testpoint['foo']

    assert 'foo' not in testpoint

    with pytest.raises(KeyError):
        del testpoint['foo']


def test_deletion_func(testpoint):
    @testpoint('foo')
    def foo_point(data): ...

    del testpoint[foo_point]
    assert 'foo' not in testpoint

    with pytest.raises(KeyError):
        del testpoint[foo_point]

    @testpoint('foo')  # type: ignore[no-redef]
    @testpoint('bar')
    def foo_point(data): ...

    del testpoint[foo_point]
    assert 'foo' not in testpoint
    assert 'bar' not in testpoint

    with pytest.raises(KeyError):
        del testpoint[foo_point]
