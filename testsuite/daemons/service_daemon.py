# pylint: disable=not-async-context-manager
import asyncio
import contextlib
import os
from typing import List

import aiohttp

from testsuite.daemons import spawn


BASE_COMMAND: List[str] = []
GRACEFUL_SHUTDOWN = True
POLL_RETRIES = 2000
PING_REQUEST_TIMEOUT = 1.0


class _DummyProcess:
    def poll(self):  # pylint: disable=no-self-use
        return None


async def _service_wait(url, process, poll_retries, ping_request_timeout):
    async with aiohttp.ClientSession() as session:
        for _ in range(poll_retries):
            if await _service_wait_iteration(
                    session, url, process, ping_request_timeout,
            ):
                return True
        raise RuntimeError('service daemon is not ready')


async def _service_wait_iteration(
        session, url, process, ping_request_timeout, sleep=0.05,
):
    if process.poll() is not None:
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


def _prepare_env(env):
    result_env = os.environ.copy()
    if env is not None:
        result_env.update(env)
    asan_preload = os.getenv('ASAN_PRELOAD')
    if asan_preload is not None:
        result_env['LD_PRELOAD'] = asan_preload
    return result_env


@contextlib.asynccontextmanager
async def _service_daemon(
        args,
        check_url,
        base_command,
        graceful_shutdown,
        poll_retries,
        ping_request_timeout,
        subprocess_options=None,
        setup_service=None,
):
    options = subprocess_options or {}
    options['env'] = _prepare_env(options.get('env'))
    async with spawn.spawned(
            base_command + args,
            graceful_shutdown=graceful_shutdown,
            **options,
    ) as process:
        if setup_service is not None:
            setup_service(process)
        await _service_wait(
            check_url, process, poll_retries, ping_request_timeout,
        )
        yield process


@contextlib.asynccontextmanager
async def start(
        args,
        check_url,
        base_command=None,
        graceful_shutdown=GRACEFUL_SHUTDOWN,
        poll_retries=POLL_RETRIES,
        ping_request_timeout=PING_REQUEST_TIMEOUT,
        subprocess_options=None,
        setup_service=None,
):
    base_command = base_command or BASE_COMMAND
    async with _service_daemon(
            args,
            check_url,
            base_command=base_command,
            graceful_shutdown=graceful_shutdown,
            poll_retries=poll_retries,
            ping_request_timeout=ping_request_timeout,
            subprocess_options=subprocess_options,
            setup_service=setup_service,
    ) as process:
        yield process


@contextlib.asynccontextmanager
async def service_wait(
        args,
        check_url,
        *,
        reporter,
        base_command=None,
        ping_request_timeout=PING_REQUEST_TIMEOUT,
):
    process = _DummyProcess()
    base_command = base_command or BASE_COMMAND
    async with aiohttp.ClientSession() as session:
        if not await _service_wait_iteration(
                session, check_url, process, ping_request_timeout,
        ):
            command = ' '.join(base_command + args)
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
    yield _DummyProcess()


async def start_dummy_process():
    @contextlib.asynccontextmanager
    async def _dummy_process():
        yield _DummyProcess()

    return _dummy_process()
