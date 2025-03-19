import contextlib
import inspect
import itertools
import signal
import subprocess
import uuid
import warnings
from typing import (
    Any,
    AsyncContextManager,
    AsyncGenerator,
    Callable,
    Dict,
    Optional,
    Sequence,
    Tuple,
)

import aiohttp
import pytest

from testsuite import annotations
from testsuite._internal import fixture_class, fixture_types
from testsuite.utils import compat

from . import service_client, service_daemon, spawn
from .spawn import __tracebackhide__

SHUTDOWN_SIGNALS = {
    'SIGINT': signal.SIGINT,
    'SIGKILL': signal.SIGKILL,
    'SIGQUIT': signal.SIGQUIT,
    'SIGTERM': signal.SIGTERM,
}


class _DaemonScope:
    def __init__(self, name: str, spawn: Callable) -> None:
        self.name = name
        self._spawn = spawn

    async def spawn(self) -> 'DaemonInstance':
        manager = self._spawn()
        # For backward compatibility with older spawners
        if inspect.iscoroutine(manager):
            warnings.warn(
                f'Please rewrite your spawner into async context manager {self._spawn}',
                PendingDeprecationWarning,
            )
            manager = await manager
        process = await manager.__aenter__()
        return DaemonInstance(manager, process)


class DaemonInstance:
    process: Optional[subprocess.Popen]

    def __init__(self, owner, process) -> None:
        self.id = uuid.uuid4().hex
        self._owner = owner
        self.process = process

    async def aclose(self) -> None:
        await self._owner.__aexit__(None, None, None)


class _DaemonStore:
    cells: Dict[str, DaemonInstance]

    def __init__(self) -> None:
        self.cells = {}

    async def aclose(self) -> None:
        for daemon in self.cells.values():
            await self._close_daemon(daemon)
        self.cells = {}

    @contextlib.asynccontextmanager
    async def scope(self, name, spawn) -> AsyncGenerator[_DaemonScope, None]:
        scope = _DaemonScope(name, spawn)
        try:
            yield scope
        finally:
            daemon = self.cells.pop(name, None)
            if daemon:
                await self._close_daemon(daemon)

    async def request(self, scope: _DaemonScope) -> DaemonInstance:
        if scope.name in self.cells:
            daemon = self.cells[scope.name]
            if daemon.process is None:
                return daemon
            if daemon.process.poll() is None:
                return daemon
        await self.aclose()
        daemon = await scope.spawn()
        self.cells[scope.name] = daemon
        return daemon

    def has_running_daemons(self) -> bool:
        for daemon in self.cells.values():
            if daemon.process and daemon.process.poll() is None:
                return True
        return False

    async def _close_daemon(self, daemon: DaemonInstance):
        await daemon.aclose()


class EnsureDaemonStartedFixture(fixture_class.Fixture):
    """Fixture that starts requested service."""

    _fixture__global_daemon_store: _DaemonStore
    _fixture__testsuite_suspend_capture: Any
    _fixture_pytestconfig: Any

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._requests = set()

    async def __call__(self, scope: _DaemonScope) -> DaemonInstance:
        self._requests.add(scope.name)
        if len(self._requests) > 1:
            pytest.fail('Test requested multiple daemons: %r' % self._requests)

        if self._fixture_pytestconfig.option.service_wait:
            with self._fixture__testsuite_suspend_capture():
                return await self._fixture__global_daemon_store.request(scope)
        return await self._fixture__global_daemon_store.request(scope)


class ServiceSpawnerFactory(fixture_class.Fixture):
    _fixture_pytestconfig: Any
    _fixture_service_client_session_factory: Any
    _fixture_wait_service_started: Any

    def __call__(
        self,
        args: Sequence[str],
        *,
        base_command: Optional[Sequence[str]] = None,
        env: Optional[Dict[str, str]] = None,
        poll_retries: int = service_daemon.POLL_RETRIES,
        ping_url: Optional[str] = None,
        ping_request_timeout: float = service_daemon.PING_REQUEST_TIMEOUT,
        ping_response_codes: Tuple[int] = service_daemon.PING_RESPONSE_CODES,
        health_check: Optional[service_daemon.HealthCheckType] = None,
        subprocess_spawner: Optional[Callable[..., subprocess.Popen]] = None,
        subprocess_options: Optional[Dict[str, Any]] = None,
        setup_service: Optional[Callable[[subprocess.Popen], None]] = None,
        shutdown_signal: Optional[int] = None,
        stdout_handler=None,
        stderr_handler=None,
    ):
        """Creates service spawner asynccontextmanager factory.

        :param args: command arguments
        :param base_command: Arguments to be prepended to ``args``.
        :param env: Environment variables dictionary.
        :param poll_retries: Number of tries for service health check
        :param ping_url: service health check url, service is considered up
            when 200 received.
        :param ping_request_timeout: Timeout for ping_url request
        :param ping_response_codes: HTTP resopnse codes tuple meaning that
            service is up and running.
        :param health_check: Async function to check service is running.
        :param subprocess_spawner: callable with `subprocess.Popen` interface.
        :param subprocess_options: Custom subprocess options.
        :param setup_service: Function to be called right after service
            is started.
        :param shutdown_signal: Signal used to stop running services.
        :returns: Return asynccontextmanager factory that might be used
                  within ``register_daemon_scope`` fixture.
        """
        pytestconfig = self._fixture_pytestconfig

        shutdown_timeout = pytestconfig.option.service_shutdown_timeout
        if shutdown_signal is None:
            shutdown_signal = SHUTDOWN_SIGNALS[
                pytestconfig.option.service_shutdown_signal
            ]

        health_check = service_daemon.make_health_check(
            ping_url=ping_url,
            ping_request_timeout=ping_request_timeout,
            ping_response_codes=ping_response_codes,
            health_check=health_check,
        )

        command_args = _build_command_args(args, base_command)

        @contextlib.asynccontextmanager
        async def spawn():
            if pytestconfig.option.service_wait:
                manager = self._fixture_wait_service_started(
                    args=command_args,
                    health_check=health_check,
                )
            elif pytestconfig.option.service_disable:
                manager = service_daemon.start_dummy_process()
            else:
                manager = service_daemon.start(
                    args=command_args,
                    env=env,
                    shutdown_signal=shutdown_signal,
                    shutdown_timeout=shutdown_timeout,
                    poll_retries=poll_retries,
                    health_check=health_check,
                    session_factory=self._fixture_service_client_session_factory,
                    subprocess_options=subprocess_options,
                    setup_service=setup_service,
                    subprocess_spawner=subprocess_spawner,
                    stdout_handler=stdout_handler,
                    stderr_handler=stderr_handler,
                )
            async with manager as process:
                yield process

        return spawn


class ServiceSpawnerFixture(fixture_class.Fixture):
    _fixture_service_spawner_factory: ServiceSpawnerFactory

    def __call__(self, *args, **kwargs):
        warnings.warn(
            'service_spawner() fixture is deprecated, '
            'use  service_spawner_factory()',
            PendingDeprecationWarning,
        )
        factory = self._fixture_service_spawner_factory(*args, **kwargs)

        async def spawner():
            return factory()

        return spawner


class CreateDaemonScope(fixture_class.Fixture):
    """Create daemon scope for daemon with command to start."""

    _fixture__global_daemon_store: _DaemonStore
    _fixture_service_spawner_factory: ServiceSpawnerFactory

    def __call__(
        self,
        *,
        args: Sequence[str],
        ping_url: Optional[str] = None,
        name: Optional[str] = None,
        base_command: Optional[Sequence] = None,
        env: Optional[Dict[str, str]] = None,
        poll_retries: int = service_daemon.POLL_RETRIES,
        ping_request_timeout: float = service_daemon.PING_REQUEST_TIMEOUT,
        ping_response_codes: Tuple[int] = service_daemon.PING_RESPONSE_CODES,
        health_check: Optional[service_daemon.HealthCheckType] = None,
        subprocess_options: Optional[Dict[str, Any]] = None,
        setup_service: Optional[Callable[[subprocess.Popen], None]] = None,
        shutdown_signal: Optional[int] = None,
        stdout_handler=None,
        stderr_handler=None,
    ) -> AsyncContextManager[_DaemonScope]:
        """
        :param args: command arguments
        :param base_command: Arguments to be prepended to ``args``.
        :param env: Environment variables dictionary.
        :param poll_retries: Number of tries for service health check
        :param ping_url: service health check url, service is considered up
            when 200 received.
        :param ping_request_timeout: Timeout for ping_url request
        :param ping_response_codes: HTTP resopnse codes tuple meaning that
            service is up and running.
        :param health_check: Async function to check service is running.
        :param subprocess_options: Custom subprocess options.
        :param setup_service: Function to be called right after service
            is started.
        :param shutdown_signal: Signal used to stop running services.
        :returns: Returns internal daemon scope instance to be used with
            ``ensure_daemon_started`` fixture.
        """
        if name is None:
            name = ' '.join(args)
        return self._fixture__global_daemon_store.scope(
            name=name,
            spawn=self._fixture_service_spawner_factory(
                args=args,
                base_command=base_command,
                env=env,
                poll_retries=poll_retries,
                ping_url=ping_url,
                ping_request_timeout=ping_request_timeout,
                ping_response_codes=ping_response_codes,
                health_check=health_check,
                subprocess_options=subprocess_options,
                setup_service=setup_service,
                shutdown_signal=shutdown_signal,
                stdout_handler=stdout_handler,
                stderr_handler=stderr_handler,
            ),
        )


class CreateServiceClientFixture(fixture_class.Fixture):
    """Creates service client instance.

    Example:

    .. code-block:: python

        def my_client(create_service_client):
            return create_service_client('http://localhost:9999/')
    """

    _fixture_service_client_default_headers: Dict[str, str]
    _fixture_service_client_options: Dict[str, Any]

    def __call__(
        self,
        base_url: str,
        *,
        client_class=service_client.Client,
        **kwargs,
    ):
        """
        :param base_url: base url for http client
        :param client_class: client class to use
        :returns: ``client_class`` instance
        """
        return client_class(
            base_url,
            headers=self._fixture_service_client_default_headers,
            **self._fixture_service_client_options,
            **kwargs,
        )


ensure_daemon_started = fixture_class.create_fixture_factory(
    EnsureDaemonStartedFixture,
)
service_spawner = fixture_class.create_fixture_factory(
    ServiceSpawnerFixture,
    scope='session',
)
service_spawner_factory = fixture_class.create_fixture_factory(
    ServiceSpawnerFactory,
    scope='session',
)
create_daemon_scope = fixture_class.create_fixture_factory(
    CreateDaemonScope,
    scope='session',
)
create_service_client = fixture_class.create_fixture_factory(
    CreateServiceClientFixture,
)


@pytest.fixture(scope='session')
def wait_service_started(pytestconfig, service_client_session_factory):
    reporter = pytestconfig.pluginmanager.getplugin('terminalreporter')

    @contextlib.asynccontextmanager
    async def waiter(*, args, health_check):
        await service_daemon.service_wait(
            args=args,
            reporter=reporter,
            health_check=health_check,
            session_factory=service_client_session_factory,
        )
        yield None

    return waiter


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
        '--service-shutdown-timeout',
        help='Service shutdown timeout in seconds. Default is %(default)s',
        default=120.0,
        type=float,
    )
    group.addoption(
        '--service-shutdown-signal',
        help='Service shutdown signal. Default is %(default)s',
        default='SIGINT',
        choices=sorted(SHUTDOWN_SIGNALS.keys()),
    )


@pytest.fixture(scope='session')
def register_daemon_scope(_global_daemon_store: _DaemonStore):
    """Context manager that registers service process session.

    Yields daemon scope instance.

    :param name: service name
    :spawn spawn: asynccontextmanager service factory
    """
    return _global_daemon_store.scope


@pytest.fixture(scope='session')
def service_client_session_factory() -> service_daemon.ClientSessionFactory:
    def make_session(**kwargs):
        return aiohttp.ClientSession(**kwargs)

    return make_session


@pytest.fixture
async def service_client_session(
    service_client_session_factory,
) -> annotations.AsyncYieldFixture[aiohttp.ClientSession]:
    async with service_client_session_factory() as session:
        yield session


@pytest.fixture
def service_client_default_headers() -> Dict[str, str]:
    """Default service client headers.

    Fill free to override in your conftest.py
    """
    return {}


@pytest.fixture
def service_client_options(
    pytestconfig,
    service_client_session: aiohttp.ClientSession,
    mockserver: fixture_types.MockserverFixture,
) -> annotations.YieldFixture[Dict[str, Any]]:
    """Returns service client options dictionary."""
    yield {
        'session': service_client_session,
        'timeout': pytestconfig.option.service_timeout or None,
        'span_id_header': mockserver.span_id_header,
    }


@pytest.fixture(scope='session')
async def _global_daemon_store():
    store = _DaemonStore()
    async with compat.aclosing(store):
        yield store


@pytest.fixture(scope='session')
def _testsuite_suspend_capture(pytestconfig):
    capmanager = pytestconfig.pluginmanager.getplugin('capturemanager')

    @contextlib.contextmanager
    def suspend():
        try:
            capmanager.suspend_global_capture()
            yield
        finally:
            capmanager.resume_global_capture()

    return suspend


def _build_command_args(
    args: Sequence,
    base_command: Optional[Sequence],
) -> Tuple[str, ...]:
    return tuple(str(arg) for arg in itertools.chain(base_command or (), args))
