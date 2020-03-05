import contextlib
import typing

import aiohttp
import pytest

from testsuite.daemons import service_daemon

SERVICE_WAIT_ERROR = (
    'In order to use --service-wait flag you have to disable output capture '
    'with -s flag.'
)


class _DaemonScope:
    def __init__(self, name, spawn):
        self.name = name
        self._spawn = spawn

    async def spawn(self):
        daemon = await self._spawn()
        process = await daemon.__aenter__()
        return _DaemonInstance(daemon, process)


class _DaemonInstance:
    def __init__(self, daemon, process):
        self._daemon = daemon
        self.process = process

    async def close(self):
        await self._daemon.__aexit__(None, None, None)


class _DaemonStore:
    def __init__(self):
        self.cells = {}

    async def close(self):
        for daemon in self.cells.values():
            await daemon.close()
        self.cells = {}

    @contextlib.asynccontextmanager
    async def scope(self, name, spawn):
        scope = _DaemonScope(name, spawn)
        try:
            yield scope
        finally:
            daemon = self.cells.pop(name, None)
            if daemon:
                await daemon.close()

    async def request(self, scope):
        if scope.name in self.cells:
            daemon = self.cells[scope.name]
            if daemon.process.poll() is None:
                return daemon
        await self.close()
        daemon = await scope.spawn()
        self.cells[scope.name] = daemon
        return daemon


@pytest.fixture(scope='session')
async def _global_daemon_store(loop):
    store = _DaemonStore()
    try:
        yield store
    finally:
        await store.close()


@pytest.fixture(scope='session')
def register_daemon_scope(_global_daemon_store: _DaemonStore):
    """Context manager that registers service process session.

    Yields daemon scope instance.

    :param name: service name
    :spawn spawn: spawner function
    """
    return _global_daemon_store.scope


@pytest.fixture
def ensure_daemon_started(_global_daemon_store: _DaemonStore):
    """Fixture that starts requested service.

    :param name: service name
    """

    requests = []

    async def do_ensure_daemon_started(scope):
        requests.append(scope.name)
        if len(requests) > 1:
            pytest.fail('Test requested multiple daemons: %r' % requests)
        return await _global_daemon_store.request(scope)

    return do_ensure_daemon_started


@pytest.fixture
async def service_client_session() -> typing.AsyncGenerator[
        aiohttp.ClientSession, None,
]:
    async with aiohttp.ClientSession() as session:
        yield session


@pytest.fixture
def service_client_default_headers() -> dict:
    """Default service client headers.

    Fill free to override in your conftest.py
    """
    return {}


@pytest.fixture
def service_client_options(
        pytestconfig,
        service_client_session: aiohttp.ClientSession,
        service_client_default_headers: dict,
        mockserver,
) -> typing.Generator[dict, None, None]:
    """Returns service client options dictionary."""
    yield {
        'session': service_client_session,
        'timeout': pytestconfig.option.service_timeout or None,
        'span_id_header': mockserver.span_id_header,
        'default_headers': service_client_default_headers,
    }


@pytest.fixture(scope='session')
def service_spawner(pytestconfig):
    """Creates service spawner.

    :param args: Service executable arguments list.
    :param check_url: Service /ping url used to ensure that service
        is up and running.
    """

    reporter = pytestconfig.pluginmanager.getplugin('terminalreporter')

    def create_spawner(
            args,
            check_url,
            *,
            base_command=None,
            graceful_shutdown=service_daemon.GRACEFUL_SHUTDOWN,
            poll_retries=service_daemon.POLL_RETRIES,
            ping_request_timeout=service_daemon.PING_REQUEST_TIMEOUT,
            subprocess_options=None,
            setup_service=None,
    ):
        async def spawn():
            if pytestconfig.option.service_wait:
                # It looks like pytest 3.8's global_and_fixture_disabled would
                # help here to re-enable console output. Throw error now.
                if pytestconfig.option.capture != 'no':
                    raise RuntimeError(SERVICE_WAIT_ERROR)
                return service_daemon.service_wait(
                    args,
                    check_url,
                    reporter=reporter,
                    base_command=base_command,
                    ping_request_timeout=ping_request_timeout,
                )
            if pytestconfig.option.service_disable:
                return service_daemon.start_dummy_process()
            return service_daemon.start(
                args,
                check_url,
                base_command=base_command,
                graceful_shutdown=graceful_shutdown,
                poll_retries=poll_retries,
                ping_request_timeout=ping_request_timeout,
                subprocess_options=subprocess_options,
                setup_service=setup_service,
            )

        return spawn

    return create_spawner


def pytest_addoption(parser):
    group = parser.getgroup('services')
    group.addoption(
        '--service-timeout',
        metavar='TIMEOUT',
        help=(
            'Service client timeout in seconds. 0 means no timeout. '
            'Default is %(default)s'
        ),
        default=120.0,
        type=float,
    )
    group.addoption(
        '--service-disable',
        action='store_true',
        help='Do not start service daemon from testsuite',
    )
    group.addoption(
        '--service-wait',
        action='store_true',
        help='Wait for service to start outside of testsuite itself, e.g. gdb',
    )
    group.addoption(
        '--service-log-level',
        choices=['debug', 'info', 'warning', 'error', 'critical'],
    )
