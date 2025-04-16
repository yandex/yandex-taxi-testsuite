import asyncio
import json
import socket

import pytest

from testsuite import asyncio_socket, logcapture


@pytest.fixture
async def logcapture_server(json_loads):
    def _parse_log_line(line):
        return json_loads(line)

    server = logcapture.CaptureServer(
        log_level=logcapture.LogLevel.INFO,
        parse_line=_parse_log_line,
    )
    async with server.start(host='localhost', port=0):
        yield server


@pytest.fixture
def logger_service(logcapture_server):
    async def logger(docs):
        socknames = logcapture_server.getsocknames()
        assert socknames

        host, port, *_ = socknames[0]
        for addr in await asyncio_socket.getaddrinfo(
            host, port, type=socket.SOCK_STREAM
        ):
            sock = asyncio_socket.create_socket(addr[0], addr[1])
            break
        else:
            pytest.fail('Failed to create socket')

        with sock:
            await sock.connect((host, port))
            for doc in docs:
                msg = json.dumps(doc) + '\n'
                await sock.sendall(msg.encode())

    return logger


async def test_select(logcapture_server, logger_service):
    async with logcapture_server.capture() as capture:
        logger_task = asyncio.create_task(
            logger_service(
                [{'level': 'INFO', 'foo': 1}, {'level': 'INFO', 'foo': 2}]
            )
        )
        await logcapture_server.wait_for_client()
        await logger_task

    records = capture.select()
    assert records == [{'level': 'INFO', 'foo': 1}, {'level': 'INFO', 'foo': 2}]

    records = capture.select(foo=2)
    assert records == [{'level': 'INFO', 'foo': 2}]


async def test_select_incorrect_usage(logcapture_server, logger_service):
    async with logcapture_server.capture() as capture:
        with pytest.raises(logcapture.IncorrectUsageError):
            capture.select()


async def test_subscribe(logcapture_server, logger_service):
    async with logcapture_server.capture() as capture:
        logger_task = asyncio.create_task(
            logger_service(
                [{'level': 'INFO', 'foo': 1}, {'level': 'INFO', 'foo': 2}]
            )
        )

        @capture.subscribe(foo=1)
        def log_handler(**kwargs):
            assert kwargs == {'level': 'INFO', 'foo': 1}

        await logcapture_server.wait_for_client()
        await logger_task

    assert log_handler.times_called == 1


async def test_subscribe_incorrect_usage(logcapture_server, logger_service):
    async with logcapture_server.capture() as capture:
        ...

    with pytest.raises(logcapture.IncorrectUsageError):

        @capture.subscribe()
        def log_handler(**kwargs): ...
