import pytest


@pytest.fixture(scope='session')
async def _echo_server(create_tcp_mockserver):
    async with create_tcp_mockserver(host='localhost', port=0) as mockserver:
        yield mockserver


@pytest.fixture
def echo_server(_echo_server):
    async def handle_client(reader, writer):
        while True:
            data = await reader.read(100)
            if not data:
                return
            writer.write(data)
            await writer.drain()

    with _echo_server.client_handler(handle_client):
        yield


@pytest.fixture
async def echo_server_connect(_echo_server):
    return _echo_server.open_connection


async def test_echo(echo_server, echo_server_connect):
    async with echo_server_connect() as (reader, writer):
        for original_data in b'foo', b'bar':
            writer.write(original_data)
            await writer.drain()

            data = await reader.read(100)
            assert data == original_data
