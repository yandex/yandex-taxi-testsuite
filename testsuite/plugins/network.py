import contextlib
import errno
import itertools
import socket
import typing

import pytest


class BaseError(Exception):
    """Base class for errors from this module."""


class NoEnabledPorts(BaseError):
    """Raised if there are not free ports for worker"""


@pytest.fixture(scope='session')
def get_free_port() -> typing.Callable[[], int]:
    """
    Returns an ephemeral TCP port that is free for IPv4 and for IPv6.

    Provides strong guarantee that no other application could bind
    to that port via bind(('', 0)).
    """

    sock_list = set()
    socket_af = socket.AF_INET
    if hasattr(socket, 'AF_INET6'):
        socket_af = socket.AF_INET6

    def _get_free_port():
        nonlocal socket_af
        nonlocal sock_list

        sock = socket.socket(socket_af, socket.SOCK_STREAM)
        addr = ('127.0.0.1' if socket_af == socket.AF_INET else '::', 0)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(addr)
            sock_list.add(sock)
            return sock.getsockname()[1]
        except OSError as err:
            if socket_af != socket.AF_INET:
                if err.errno == errno.EADDRNOTAVAIL:
                    socket_af = socket.AF_INET
                    return _get_free_port()

        raise NoEnabledPorts()

    try:
        yield _get_free_port
    finally:
        for sock in sock_list:
            sock.close()
