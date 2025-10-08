import pathlib
import sys

import pytest

from testsuite.daemons import service_client
from testsuite.utils import net as net_utils

HTTPD_PATH = pathlib.Path(__file__).parent / 'daemons/httpd.py'


def getbaseurl(socket):
    addr, port = socket.getsockname()
    return f'http://{addr}:{port}'


@pytest.fixture(scope='session')
async def create_service_scope(register_daemon_scope, service_spawner_factory):
    def create_scope(name, socket):
        return register_daemon_scope(
            name=name,
            spawn=service_spawner_factory(
                [
                    sys.executable,
                    HTTPD_PATH,
                    '--server-fd',
                    str(socket.fileno()),
                    '--who',
                    name,
                ],
                ping_url=getbaseurl(socket) + '/ping',
                subprocess_options={'pass_fds': [socket.fileno()]},
            ),
            multiple=True,
        )

    return create_scope


@pytest.fixture
def create_httpd_client(
    service_client_default_headers,
    service_client_options,
):
    def create(baseurl):
        return service_client.Client(
            baseurl,
            headers=service_client_default_headers,
            **service_client_options,
        )

    return create


@pytest.fixture(scope='session')
def service1_sock():
    with net_utils.bind_socket() as sock:
        yield sock


@pytest.fixture(scope='session')
def service2_sock():
    with net_utils.bind_socket() as sock:
        yield sock


@pytest.fixture(scope='session')
def service1_baseurl(service1_sock):
    return getbaseurl(service1_sock)


@pytest.fixture(scope='session')
def service2_baseurl(service2_sock):
    return getbaseurl(service2_sock)


@pytest.fixture(scope='session')
async def service1_scope(create_service_scope, service1_sock):
    async with create_service_scope('service1', service1_sock) as scope:
        return scope


@pytest.fixture(scope='session')
async def service2_scope(create_service_scope, service2_sock):
    async with create_service_scope('service2', service2_sock) as scope:
        return scope


@pytest.fixture
def service1_client(create_httpd_client, service1_baseurl):
    return create_httpd_client(service1_baseurl)


@pytest.fixture
def service2_client(create_httpd_client, service2_baseurl):
    return create_httpd_client(service2_baseurl)


async def test_multiple_instances(
    ensure_daemon_started,
    service1_scope,
    service2_scope,
    service1_client,
    service2_client,
):
    service1 = await ensure_daemon_started(service1_scope)
    service2 = await ensure_daemon_started(service2_scope)
    assert service1.process.pid != service2.process.pid

    response = await service1_client.get('/hello')
    assert response.status_code == 200
    assert response.content == b'Hello, service1!\n'

    response = await service2_client.get('/hello')
    assert response.status_code == 200
    assert response.content == b'Hello, service2!\n'
