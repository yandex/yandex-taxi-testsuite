import pathlib
import sys

import pytest

from testsuite.databases.mysql import discover


pytest_plugins = [
    'testsuite.pytest_plugin',
    'testsuite.databases.mysql.pytest_plugin',
]


def pytest_addoption(parser):
    group = parser.getgroup('Example service')
    group.addoption(
        '--example-service-port',
        help='Bind example services to this port (default is %(default)s)',
        default=8080,
        type=int,
    )


@pytest.fixture
async def example_service(
        ensure_daemon_started,
        # Service process holder
        example_service_scope,
        # Service dependencies
        mockserver,
        mysql,
):
    # Start service if not started yet
    await ensure_daemon_started(example_service_scope)


@pytest.fixture
async def example_client(
        create_service_client, example_service_baseurl, example_service,
):
    # Create service client instance
    return create_service_client(example_service_baseurl)


@pytest.fixture(scope='session')
def example_service_baseurl(pytestconfig):
    return f'http://localhost:{pytestconfig.option.example_service_port}/'


@pytest.fixture(scope='session')
def example_root():
    """Path to example service root."""
    return pathlib.Path(__file__).parent.parent


@pytest.fixture(scope='session')
async def example_service_scope(
        pytestconfig,
        create_daemon_scope,
        example_root,
        example_service_baseurl,
        mysql_local,
        mysql_conninfo,
):
    async with create_daemon_scope(
            args=[
                sys.executable,
                str(example_root.joinpath('server.py')),
                '--port',
                str(pytestconfig.option.example_service_port),
                '--mysql-host',
                mysql_conninfo.hostname,
                '--mysql-port',
                str(mysql_conninfo.port),
                '--mysql-user',
                mysql_conninfo.user,
                '--mysql-dbname',
                mysql_local['chat_messages'].dbname,
            ],
            ping_url=example_service_baseurl + 'ping',
    ) as scope:
        yield scope


@pytest.fixture(scope='session')
def mysql_local(example_root):
    return discover.find_schemas([example_root.joinpath('schemas/mysql')])
