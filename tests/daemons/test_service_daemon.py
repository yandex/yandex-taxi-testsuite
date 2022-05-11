import pathlib
import sys

import pytest

from testsuite.daemons import service_daemon
from testsuite.daemons import spawn
from testsuite.utils import callinfo


@pytest.fixture
def dummy_daemon(mockserver):
    class Daemon:
        path = pathlib.Path(__file__).parent / 'daemons/dummy_daemon.py'
        ping_url = mockserver.url('my-service/ping')

    return Daemon()


@pytest.fixture
def logger_plugin(pytestconfig):
    return pytestconfig.pluginmanager.getplugin('testsuite_logger')


async def test_service_daemon(mockserver, dummy_daemon, logger_plugin):
    @mockserver.handler('/my-service/ping')
    def ping_handler(request):
        if ping_handler.times_called < 1:
            return mockserver.make_response('Not ready', 503)
        return mockserver.make_response()

    async with service_daemon.start(
            [sys.executable, dummy_daemon.path],
            health_check=service_daemon.make_health_check(
                ping_url=dummy_daemon.ping_url,
            ),
            logger_plugin=logger_plugin,
    ):
        pass

    assert ping_handler.times_called == 2


async def test_service_daemon_custom_health(
        mockserver, dummy_daemon, logger_plugin,
):
    @callinfo.acallqueue
    @service_daemon.health_check_with_timeout
    async def health_check(*, process, session):
        return health_check.times_called > 0

    async with service_daemon.start(
            args=[sys.executable, dummy_daemon.path],
            logger_plugin=logger_plugin,
            health_check=health_check,
    ):
        pass

    assert health_check.times_called == 2


async def test_service_wait_custom_health(
        mockserver,
        dummy_daemon,
        logger_plugin,
        pytestconfig,
        wait_service_started,
):
    @callinfo.acallqueue
    @service_daemon.health_check_with_timeout
    async def health_check(*, process, session):
        return health_check.times_called > 0

    async with wait_service_started(
            args=[sys.executable, str(dummy_daemon.path)],
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
        mockserver, dummy_daemon, daemon_args, expected_message, logger_plugin,
):
    @mockserver.handler('/my-service/ping')
    def _ping_handler(request):
        return mockserver.make_response('Not ready', 503)

    with pytest.raises(spawn.ExitCodeError) as exc:
        start_command = [dummy_daemon.path] + daemon_args
        async with service_daemon.start(
                start_command,
                health_check=service_daemon.make_health_check(
                    ping_url=dummy_daemon.ping_url,
                ),
                logger_plugin=logger_plugin,
        ):
            pass

    assert exc.value.args == (expected_message,)
