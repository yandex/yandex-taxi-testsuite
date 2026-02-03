import platform
from typing import Any

import aiohttp
import pytest

import testsuite
from testsuite.daemons import service_client
from testsuite.mockserver import classes, server


@pytest.fixture
async def my_mockserver(
    asyncexc_append,
    _my_mockserver: server.Server,
    mockserver_create_session,
    testsuite_traceid_manager,
):
    with mockserver_create_session(_my_mockserver) as session:
        yield session


@pytest.fixture(scope='session')
async def _my_mockserver(pytestconfig):
    async with server.create_server(
        host='localhost', port=0, pytestconfig=pytestconfig
    ) as srv:
        yield srv


@pytest.fixture
async def my_mockserver_client(
    my_mockserver: testsuite.MockserverFixture,
    service_client_options,
) -> service_client.Client:
    return service_client.Client(
        my_mockserver.base_url,
        **service_client_options,
    )


async def test_handler(my_mockserver, my_mockserver_client):
    @my_mockserver.handler('/test')
    def _test(request: testsuite.MockserverRequest):
        return my_mockserver.make_response('test', 200)

    response = await my_mockserver_client.get('/test')
    assert response.status_code == 200
    assert response.content == b'test'
