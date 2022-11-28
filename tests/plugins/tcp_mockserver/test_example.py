import contextlib

import pytest


@pytest.fixture(scope='session')
async def _tcp_mockserver(create_tcp_mockserver):
    """
    Returns base per-session server instance bound to random port.
    """
    async with create_tcp_mockserver(host='localhost', port=0) as mockserver:
        yield mockserver


@pytest.fixture
def tcp_mockserver(_tcp_mockserver):
    """
    Returns per-test mockserver interface.
    """

    async def handle_client(reader, writer):
        writer.write(b'Hello, world!')
        await writer.drain()
        writer.close()

    with _tcp_mockserver.client_handler(handle_client):
        yield


@pytest.fixture
async def tcp_mockserver_connect(_tcp_mockserver):
    """Create connection to the tcp mockserver."""
    return _tcp_mockserver.open_connection


async def test_server(tcp_mockserver, tcp_mockserver_connect):
    async with tcp_mockserver_connect() as (reader, _):
        data = await reader.read()
        assert data == b'Hello, world!'
