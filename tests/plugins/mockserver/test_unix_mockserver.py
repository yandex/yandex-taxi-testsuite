import aiohttp
import pytest
import platform

from testsuite._internal import fixture_types
from testsuite.daemons import service_client
from testsuite.mockserver import classes
from testsuite.mockserver import server
from typing import Any
from typing import Dict

if platform.system() == 'Darwin':
    _MOCKSERVER_SOCKET = 'socket'
else:
    _MOCKSERVER_SOCKET = 'mockserver.socket'


@pytest.fixture
def unix_mockserver(
    asyncexc_append,
    _unix_mockserver: server.Server,
    _mockserver_trace_id: str,
):
    with _unix_mockserver.new_session(
        asyncexc_append=asyncexc_append,
        trace_id=_mockserver_trace_id,
    ) as session:
        yield server.MockserverFixture(_unix_mockserver, session)


@pytest.fixture(scope='session')
async def _unix_mockserver(pytestconfig, tmp_path_factory):
    async with server.create_unix_server(
        tmp_path_factory.mktemp('mockserver') / _MOCKSERVER_SOCKET,
        loop=None,
        pytestconfig=pytestconfig,
    ) as result:
        yield result


@pytest.fixture(scope='session')
def unix_mockserver_info(
    _unix_mockserver: server.Server,
) -> classes.MockserverInfo:
    return _unix_mockserver.server_info


@pytest.fixture
async def unix_mockserver_client(
    unix_mockserver: fixture_types.MockserverFixture,
    unix_mockserver_info: classes.MockserverInfo,
    service_client_options: Dict[str, Any],
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
    unix_mockserver: fixture_types.MockserverFixture,
    unix_mockserver_client: service_client.Client,
):
    @unix_mockserver.handler('/test_unix_socket')
    def _test(request: fixture_types.MockserverRequest):
        return unix_mockserver.make_response('test', 200)

    response = await unix_mockserver_client.get('test_unix_socket')
    assert response.status_code == 200
    assert response.content == b'test'
