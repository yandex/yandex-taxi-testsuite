# pylint: disable=not-async-context-manager
import asyncio
import os
import signal
import subprocess
import time
from typing import AsyncGenerator
from typing import Awaitable
from typing import Callable
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Tuple

import aiohttp

from testsuite.daemons import spawn
from testsuite.utils import compat


POLL_RETRIES = 2000
PING_REQUEST_TIMEOUT = 1.0
PING_RESPONSE_CODES = (200,)

HealthCheckType = Callable[..., Awaitable[bool]]

ClientSessionFactory = Callable[..., aiohttp.ClientSession]


@compat.asynccontextmanager
async def start(
        args: Sequence[str],
        *,
        health_check: HealthCheckType,
        session_factory: ClientSessionFactory = aiohttp.ClientSession,
        logger_plugin,
        env: Optional[Dict[str, str]] = None,
        shutdown_signal: int = signal.SIGINT,
        shutdown_timeout: float = 120,
        poll_retries: int = POLL_RETRIES,
        subprocess_options=None,
        setup_service=None,
        subprocess_spawner=None,
        stdout_handler=None,
        stderr_handler=None,
) -> AsyncGenerator[Optional[subprocess.Popen], None]:
    with logger_plugin.temporary_suspend() as log_manager:
        async with session_factory() as session:
            async with _service_daemon(
                    args=args,
                    env=env,
                    shutdown_signal=shutdown_signal,
                    shutdown_timeout=shutdown_timeout,
                    poll_retries=poll_retries,
                    subprocess_options=subprocess_options,
                    setup_service=setup_service,
                    subprocess_spawner=subprocess_spawner,
                    health_check=health_check,
                    session=session,
                    stdout_handler=stdout_handler,
                    stderr_handler=stderr_handler,
            ) as process:
                log_manager.clear()
                log_manager.resume()
                yield process


async def service_wait(
        args: Sequence[str],
        *,
        health_check: HealthCheckType,
        session_factory: ClientSessionFactory = aiohttp.ClientSession,
        reporter,
):
    process = None
    flush_supported = hasattr(reporter, 'flush')
    async with session_factory() as session:
        if not await _run_health_check(
                health_check, session=session, process=process,
        ):
            command = ' '.join(args)
            reporter.write_line('')
            reporter.write_line(
                'Service is not running yet you may want to start it from '
                'outside of testsuite, e.g. using gdb:',
                yellow=True,
            )
            reporter.write_line('')
            reporter.write_line('gdb --args {}'.format(command), green=True)
            reporter.write_line('')
            reporter.write('Waiting for service to start...')
            while not await _run_health_check(
                    health_check, session=session, process=process, sleep=0.2,
            ):
                reporter.write('.')
                if flush_supported:
                    reporter.flush()
            reporter.write_line('')


async def start_dummy_process():
    @compat.asynccontextmanager
    async def _dummy_process():
        yield None

    return _dummy_process()


def make_health_check(
        *,
        health_check: Optional[HealthCheckType] = None,
        ping_url: Optional[str],
        ping_request_timeout: float = PING_REQUEST_TIMEOUT,
        ping_response_codes: Tuple[int] = PING_RESPONSE_CODES,
) -> HealthCheckType:
    if ping_url:
        return _make_ping_health_check(
            ping_url=ping_url,
            ping_request_timeout=ping_request_timeout,
            ping_response_codes=ping_response_codes,
        )
    if health_check:
        return health_check

    raise RuntimeError('Either `ping_url` or `health_check` must be set')


async def _run_health_check(
        health_check: HealthCheckType,
        *,
        session: aiohttp.ClientSession,
        process: Optional[subprocess.Popen],
        sleep: float = 0.05,
):
    if process and process.poll() is not None:
        raise spawn.exit_code_error(process.poll())

    begin = time.perf_counter()
    if await health_check(session=session, process=process):
        return True
    end = time.perf_counter()
    to_sleep = begin + sleep - end
    if to_sleep > 0:
        await asyncio.sleep(to_sleep)
    return False


def _make_ping_health_check(
        *,
        ping_url: str,
        ping_request_timeout: float,
        ping_response_codes: Tuple[int],
) -> HealthCheckType:
    async def ping_health_check(
            session: aiohttp.ClientSession,
            process: Optional[subprocess.Popen],
    ) -> bool:
        try:
            response = await session.get(
                ping_url, timeout=ping_request_timeout,
            )
            if response.status in ping_response_codes:
                return True
        except asyncio.TimeoutError:
            return False  # skip sleep as we've waited enough
        except aiohttp.ClientConnectorError:
            pass
        return False

    return ping_health_check


async def _service_wait(
        process: Optional[subprocess.Popen],
        *,
        poll_retries: int,
        health_check: HealthCheckType,
        session: aiohttp.ClientSession,
) -> bool:
    for _ in range(poll_retries):
        if await _run_health_check(
                health_check, session=session, process=process,
        ):
            return True
    raise RuntimeError('service daemon is not ready')


def _prepare_env(*envs: Optional[Dict[str, str]]) -> Dict[str, str]:
    result = os.environ.copy()
    for env in envs:
        if env is not None:
            result.update(env)
    asan_preload = os.getenv('ASAN_PRELOAD')
    if asan_preload is not None:
        result['LD_PRELOAD'] = asan_preload
    return result


@compat.asynccontextmanager
async def _service_daemon(
        args: Sequence[str],
        *,
        env: Optional[Dict[str, str]],
        shutdown_signal: int,
        shutdown_timeout: float,
        poll_retries: int,
        subprocess_options=None,
        setup_service=None,
        subprocess_spawner=None,
        health_check,
        session: aiohttp.ClientSession,
        stdout_handler=None,
        stderr_handler=None,
) -> AsyncGenerator[subprocess.Popen, None]:
    options = subprocess_options.copy() if subprocess_options else {}
    options['env'] = _prepare_env(env, options.get('env'))
    async with spawn.spawned(
            args,
            shutdown_signal=shutdown_signal,
            shutdown_timeout=shutdown_timeout,
            subprocess_spawner=subprocess_spawner,
            stdout_handler=stdout_handler,
            stderr_handler=stderr_handler,
            **options,
    ) as process:
        if setup_service is not None:
            setup_service(process)
        await _service_wait(
            process=process,
            poll_retries=poll_retries,
            health_check=health_check,
            session=session,
        )
        yield process
