import asyncio
import socket

from . import compat

DEFAULT_BACKLOG = 50


@compat.asynccontextmanager
async def create_server(factory, *, loop=None, **kwargs):
    if loop is None:
        loop = _get_running_loop()
    server = await loop.create_server(factory, **kwargs)
    try:
        yield server
    finally:
        server.close()
        await server.wait_closed()


def create_tcp_server(
        factory, *, loop=None, host='localhost', port=0, sock=None, **kwargs,
):
    if sock is None:
        sock = bind_socket(host, port)
    return create_server(factory, loop=loop, sock=sock, **kwargs)


def bind_socket(
        hostname='localhost',
        port=0,
        family=socket.AF_INET,
        backlog=DEFAULT_BACKLOG,
):
    sock = socket.socket(family)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((hostname, port))
    sock.listen(backlog)
    return sock


if hasattr(asyncio, 'get_running_loop'):
    _get_running_loop = asyncio.get_running_loop
else:
    _get_running_loop = asyncio.get_event_loop
