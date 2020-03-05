# pylint: disable=not-async-context-manager
import os.path

import pytest

from testsuite.daemons import service_daemon
from testsuite.daemons import spawn


@pytest.fixture
def dummy_daemon(mockserver):
    class Daemon:
        path = os.path.join(
            os.path.dirname(__file__), 'daemons', 'dummy_daemon',
        )
        ping_url = mockserver.url('my-service/ping')

    return Daemon()


async def test_service_daemon(mockserver, dummy_daemon):
    @mockserver.handler('/my-service/ping')
    def ping_handler(request):
        if ping_handler.times_called < 1:
            return mockserver.make_response('Not ready', 503)
        return mockserver.make_response()

    async with service_daemon.start(
            [dummy_daemon.path], dummy_daemon.ping_url,
    ):
        pass

    assert ping_handler.times_called == 2


@pytest.mark.parametrize(
    'daemon_args,expected_message',
    [
        (['--raise-signal', '15'], 'Daemon was killed by SIGTERM signal'),
        (['--exit-code', '1'], 'Daemon exited with status code 1'),
    ],
)
async def test_service_daemon_failure(
        mockserver, dummy_daemon, daemon_args, expected_message,
):
    @mockserver.handler('/my-service/ping')
    def _ping_handler(request):
        return mockserver.make_response('Not ready', 503)

    with pytest.raises(spawn.ExitCodeError) as exc:
        start_command = [dummy_daemon.path] + daemon_args
        async with service_daemon.start(start_command, dummy_daemon.ping_url):
            pass

    assert exc.value.args == (expected_message,)
