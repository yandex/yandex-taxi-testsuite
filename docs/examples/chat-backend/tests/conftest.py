import pathlib
import sys

import pytest

pytest_plugins = ['testsuite.pytest_plugin']


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
        mockserver_info,
        example_root,
        example_service_baseurl,
):
    async with create_daemon_scope(
            args=[
                sys.executable,
                str(example_root.joinpath('server.py')),
                '--port',
                str(pytestconfig.option.example_service_port),
                '--storage-service-url',
                mockserver_info.base_url + 'storage/',
            ],
            check_url=example_service_baseurl + 'ping',
    ) as scope:
        yield scope
