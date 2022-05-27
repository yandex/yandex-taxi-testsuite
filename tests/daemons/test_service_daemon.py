# pylint: disable=protected-access
import io
import pathlib
import select
import subprocess
import sys

import aiohttp
import pytest

from testsuite.daemons import service_daemon
from testsuite.daemons import spawn
from testsuite.utils import callinfo


def is_output_read(file):
    rlist, _, _ = select.select([file.fileno()], (), (), 0)
    return bool(rlist)


@pytest.fixture
def health_check():
    stdout_buf = io.BytesIO()

    @callinfo.acallqueue
    async def health_check(*, process, session):
        if not process:
            pytest.fail('process does not exist')
        if not process.stdout:
            pytest.fail('process.stdout is not set')
        if is_output_read(process.stdout):
            stdout_buf.write(process.stdout.read(100))
        return stdout_buf.getvalue() == b'ready\n'

    return health_check


@pytest.fixture
def dummy_daemon(mockserver):
    return pathlib.Path(__file__).parent / 'daemons/dummy_daemon.py'


@pytest.fixture
def logger_plugin(pytestconfig):
    return pytestconfig.pluginmanager.getplugin('testsuite_logger')


async def test_service_daemon(
        mockserver, dummy_daemon, logger_plugin, health_check,
):
    async with service_daemon.start(
            args=[sys.executable, dummy_daemon],
            logger_plugin=logger_plugin,
            health_check=health_check,
            subprocess_options={'stdout': subprocess.PIPE, 'bufsize': 0},
    ):
        pass

    assert health_check.times_called > 0


async def test_service_wait_custom_health(
        mockserver,
        dummy_daemon,
        logger_plugin,
        pytestconfig,
        wait_service_started,
):
    @callinfo.acallqueue
    async def health_check(*, process, session):
        return health_check.times_called > 0

    async with wait_service_started(
            args=[sys.executable, str(dummy_daemon)],
            health_check=health_check,
    ):
        pass

    assert health_check.times_called == 2


@pytest.mark.parametrize(
    'daemon_args,expected_message',
    [
        (['--raise-signal', '6'], 'Service aborted by SIGABRT signal'),
        (
            ['--raise-signal', '11'],
            'Service crashed with SIGSEGV signal (segmentation fault)',
        ),
        (['--raise-signal', '15'], 'Service terminated by SIGTERM signal'),
        (['--exit-code', '1'], 'Service exited with status code 1'),
    ],
)
async def test_service_daemon_failure(
        mockserver,
        dummy_daemon,
        daemon_args,
        expected_message,
        logger_plugin,
        health_check,
):
    with pytest.raises(spawn.ExitCodeError) as exc:
        start_command = [dummy_daemon] + daemon_args
        async with service_daemon.start(
                start_command,
                health_check=health_check,
                logger_plugin=logger_plugin,
                subprocess_options={'stdout': subprocess.PIPE, 'bufsize': 0},
        ):
            pass

    assert exc.value.args == (expected_message,)


async def test_ping_health_checker(mockserver):
    @mockserver.handler('my-service/ping')
    def ping_handler(request):
        if ping_handler.times_called < 1:
            return mockserver.make_response('Not ready', 503)
        return mockserver.make_response()

    checker = service_daemon._make_ping_health_check(
        ping_url=mockserver.url('my-service/ping'),
        ping_request_timeout=1.0,
        ping_response_codes=(200,),
    )
    async with aiohttp.ClientSession() as session:
        assert not await checker(session=session, process=None)
        assert ping_handler.times_called == 1

        assert await checker(session=session, process=None)
        assert ping_handler.times_called == 2


@pytest.mark.parametrize('status,expected', [(False, False), (True, True)])
async def test_run_health_check(status, expected):
    class Process:
        def poll(self):
            return None

    async def health_check(*, session, process):
        return status

    async with aiohttp.ClientSession() as session:
        assert (
            await service_daemon._run_health_check(
                health_check, session=session, process=Process(),
            )
            is expected
        )


async def test_run_health_check_poll_failed():
    class Process:
        def poll(self):
            return 123

    async def health_check(*, session, process):
        return False

    async with aiohttp.ClientSession() as session:
        with pytest.raises(spawn.ExitCodeError) as exc:
            await service_daemon._run_health_check(
                health_check, session=session, process=Process(),
            )
        assert exc.value.exit_code == 123
