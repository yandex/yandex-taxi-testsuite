import pathlib
import sys

import pytest

from testsuite.daemons import spawn


@pytest.fixture
def simple_daemon(mockserver):
    return str(pathlib.Path(__file__).parent / 'daemons/simple.py')


async def test_spawn(simple_daemon):
    async with spawn.spawned([sys.executable, simple_daemon, 'pass']) as process:
        process.wait()

    assert process.returncode == 0


async def test_spawn_outerr(simple_daemon):
    out = []
    err = []

    def handle_stdout(line):
        out.append(line)

    def handle_stderr(line):
        err.append(line)

    async with spawn.spawned(
            [sys.executable, simple_daemon, 'stdout'],
            stdout_handler=handle_stdout,
            stderr_handler=handle_stderr,
    ) as process:
        process.wait()

    assert process.returncode == 0
    assert out == [b'out0\n', b'out1\n', b'out2\n']
    assert err == [b'err0\n', b'err1\n', b'err2\n']
