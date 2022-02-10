import pathlib
import sys

import pytest

from testsuite.daemons import pytest_plugin
from testsuite.daemons import service_client
from testsuite.daemons import service_daemon
from testsuite.utils import net as net_utils

HTTPD_NAME = f'{__name__}.httpd'
HTTPD_PATH = pathlib.Path(__file__).parent / 'daemons/httpd.py'


@pytest.fixture(scope='session')
def httpd_socket():
    with net_utils.bind_socket() as sock:
        yield sock


@pytest.fixture(scope='session')
def httpd_baseurl(httpd_socket):
    _, port = httpd_socket.getsockname()
    return 'http://localhost:%d' % (port,)


@pytest.fixture(scope='session')
async def httpd_scope(
        register_daemon_scope, httpd_baseurl, httpd_socket, service_spawner,
):
    async with register_daemon_scope(
            name=HTTPD_NAME,
            spawn=service_spawner(
                [
                    sys.executable,
                    HTTPD_PATH,
                    '--server-fd',
                    str(httpd_socket.fileno()),
                ],
                httpd_baseurl + '/ping',
                subprocess_options={'pass_fds': [httpd_socket.fileno()]},
            ),
    ) as scope:
        yield scope


@pytest.fixture
async def httpd(ensure_daemon_started, mockserver, httpd_scope):
    return await ensure_daemon_started(httpd_scope)


@pytest.fixture
def httpd_client(
        httpd,
        httpd_baseurl,
        service_client_default_headers,
        service_client_options,
):
    return service_client.Client(
        httpd_baseurl,
        headers=service_client_default_headers,
        **service_client_options,
    )


async def test_httpd_hello(httpd_client):
    response = await httpd_client.get('/hello')
    assert response.status_code == 200
    assert response.content == b'Hello, world!\n'


@pytest.mark.parametrize('restart_id', [0, 1])
async def test_httpd_restart(
        httpd_client, restart_id, httpd: pytest_plugin.DaemonInstance,
):
    response = await httpd_client.get('/exit')
    assert response.status_code == 200
    assert response.content == b'Exiting!\n'
    if httpd.process:
        httpd.process.wait(timeout=1.0)


async def test_daemon_disabled(
        register_daemon_scope, ensure_daemon_started, mockserver,
):
    @mockserver.handler('/my-daemon/ping')
    def _ping_handler(request):
        return mockserver.make_response()

    async with register_daemon_scope(
            '%s.daemon-disabled' % __name__,
            spawn=service_daemon.start_dummy_process,
    ) as scope:
        await ensure_daemon_started(scope)


async def test_ensure_daemon_started_repeatable(
        ensure_daemon_started, mockserver, httpd_scope,
):
    instance1 = await ensure_daemon_started(httpd_scope)
    instance2 = await ensure_daemon_started(httpd_scope)
    assert instance1.process.pid == instance2.process.pid
