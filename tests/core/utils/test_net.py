import errno
import socket

import pytest

from testsuite.utils import net


def test_bind_multiple():
    ports = set()
    with net.close_sockets(net.bind_socket_multiple()) as socks:
        for sock in socks:
            sock_port = sock.getsockname()[1]
            ports.add(sock_port)
    assert len(ports) == 1


def test_bind_multiple_addrinuse():
    with net.bind_socket() as sock1:
        port = sock1.getsockname()[1]
        with pytest.raises(socket.error) as exc:
            net.bind_socket_multiple(port=port)
        assert exc.value.errno == errno.EADDRINUSE


async def test_server_multiple():
    def factory(): ...

    with net.close_sockets(net.bind_socket_multiple()) as socks:
        async with net.create_server_multiple(factory, socks) as server:
            pass
