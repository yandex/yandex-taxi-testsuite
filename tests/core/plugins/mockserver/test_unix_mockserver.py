import platform
from typing import Any

import aiohttp
import pytest

import testsuite
from testsuite.daemons import service_client
from testsuite.mockserver import server

if platform.system() == 'Darwin':
    _MOCKSERVER_SOCKET = 'socket'
else:
    _MOCKSERVER_SOCKET = 'mockserver.socket'


@pytest.fixture
async def unix_mockserver(
    _unix_mockserver: server.Server,
    mockserver_create_session,
):
    with mockserver_create_session(_unix_mockserver) as session:
        yield session


@pytest.fixture(scope='session')
async def _unix_mockserver(tmp_path_factory, mockserver_create):
    socket_path = tmp_path_factory.mktemp('mockserver') / _MOCKSERVER_SOCKET
    async with mockserver_create(socket_path=socket_path) as server:
        yield server


@pytest.fixture(scope='session')
def unix_mockserver_info(
    _unix_mockserver: server.Server,
) -> testsuite.MockserverInfo:
    return _unix_mockserver.server_info


@pytest.fixture
async def unix_mockserver_client(
    unix_mockserver: testsuite.MockserverFixture,
    unix_mockserver_info: testsuite.MockserverInfo,
    service_client_options: dict[str, Any],
) -> service_client.Client:
    async with aiohttp.UnixConnector(
        path=str(unix_mockserver_info.socket_path),
    ) as conn:
        async with aiohttp.ClientSession(connector=conn) as session:
            unix_service_client_options = {
                **service_client_options,
                'session': session,
            }

            yield service_client.Client(
                unix_mockserver.base_url,
                headers={'host': str(unix_mockserver_info.socket_path)},
                **unix_service_client_options,
            )


async def test_handler(
    unix_mockserver: testsuite.MockserverFixture,
    unix_mockserver_client: service_client.Client,
):
    @unix_mockserver.handler('/test_unix_socket')
    def _test(request: testsuite.MockserverRequest):
        return unix_mockserver.make_response('test', 200)

    response = await unix_mockserver_client.get('test_unix_socket')
    assert response.status_code == 200
    assert response.content == b'test'
