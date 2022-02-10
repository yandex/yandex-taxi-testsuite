# pylint: disable=not-async-context-manager
import asyncio
import contextlib
import itertools
import os
import signal
import subprocess
from typing import AsyncGenerator
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Tuple

import aiohttp

from testsuite.daemons import spawn


POLL_RETRIES = 2000
PING_REQUEST_TIMEOUT = 1.0


@contextlib.asynccontextmanager
async def start(
        args: Sequence[str],
        check_url: str,
        *,
        logger_plugin,
        base_command: Optional[Sequence[str]] = None,
        env: Optional[Dict[str, str]] = None,
        shutdown_signal: int = signal.SIGINT,
        shutdown_timeout: float = 120,
        poll_retries: int = POLL_RETRIES,
        ping_request_timeout: float = PING_REQUEST_TIMEOUT,
        subprocess_options=None,
        setup_service=None,
) -> AsyncGenerator[Optional[subprocess.Popen], None]:
    with logger_plugin.temporary_suspend() as log_manager:
        async with _service_daemon(
                args,
                check_url,
                base_command=base_command,
                env=env,
                shutdown_signal=shutdown_signal,
                shutdown_timeout=shutdown_timeout,
                poll_retries=poll_retries,
                ping_request_timeout=ping_request_timeout,
                subprocess_options=subprocess_options,
                setup_service=setup_service,
        ) as process:
            log_manager.clear()
            log_manager.resume()
            yield process


@contextlib.asynccontextmanager
async def service_wait(
        args: Sequence[str],
        check_url: str,
        *,
        reporter,
        base_command: Optional[Sequence[str]] = None,
        ping_request_timeout: float = PING_REQUEST_TIMEOUT,
) -> AsyncGenerator[Optional[subprocess.Popen], None]:
    process = None
    base_command = base_command or []
    async with aiohttp.ClientSession() as session:
        if not await _service_wait_iteration(
                session, check_url, process, ping_request_timeout,
        ):
            command = ' '.join(_build_command_args(args, base_command))
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
            while not await _service_wait_iteration(
                    session,
                    check_url,
                    process,
                    ping_request_timeout,
                    sleep=0.2,
            ):
                reporter.write('.')
            reporter.write_line('')
    yield None


async def start_dummy_process():
    @contextlib.asynccontextmanager
    async def _dummy_process():
        yield None

    return _dummy_process()


async def _service_wait(
        url: str,
        process: Optional[subprocess.Popen],
        poll_retries: int,
        ping_request_timeout: float,
) -> bool:
    async with aiohttp.ClientSession() as session:
        for _ in range(poll_retries):
            if await _service_wait_iteration(
                    session, url, process, ping_request_timeout,
            ):
                return True
        raise RuntimeError('service daemon is not ready')


async def _service_wait_iteration(
        session: aiohttp.ClientSession,
        url: str,
        process: Optional[subprocess.Popen],
        ping_request_timeout: float,
        sleep: float = 0.05,
) -> bool:
    if process and process.poll() is not None:
        raise RuntimeError('service daemon is not running')
    try:
        response = await session.get(url, timeout=ping_request_timeout)
        if response.status == 200:
            return True
    except asyncio.TimeoutError:
        return False  # skip sleep as we've waited enough
    except aiohttp.ClientConnectorError:
        pass
    await asyncio.sleep(sleep)
    return False


def _prepare_env(*envs: Optional[Dict[str, str]]) -> Dict[str, str]:
    result = os.environ.copy()
    for env in envs:
        if env is not None:
            result.update(env)
    asan_preload = os.getenv('ASAN_PRELOAD')
    if asan_preload is not None:
        result['LD_PRELOAD'] = asan_preload
    return result


@contextlib.asynccontextmanager
async def _service_daemon(
        args: Sequence[str],
        check_url: str,
        base_command: Sequence[str],
        env: Optional[Dict[str, str]],
        shutdown_signal: int,
        shutdown_timeout: float,
        poll_retries: int,
        ping_request_timeout: float,
        subprocess_options=None,
        setup_service=None,
) -> AsyncGenerator[subprocess.Popen, None]:
    options = subprocess_options.copy() if subprocess_options else {}
    options['env'] = _prepare_env(env, options.get('env'))
    async with spawn.spawned(
            _build_command_args(args, base_command),
            shutdown_signal=shutdown_signal,
            shutdown_timeout=shutdown_timeout,
            **options,
    ) as process:
        if setup_service is not None:
            setup_service(process)
        await _service_wait(
            check_url, process, poll_retries, ping_request_timeout,
        )
        yield process


def _build_command_args(
        args: Sequence, base_command: Optional[Sequence],
) -> Tuple[str, ...]:
    return tuple(str(arg) for arg in itertools.chain(base_command or (), args))
