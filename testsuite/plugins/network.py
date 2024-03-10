import contextlib
import errno
import itertools
import platform
import socket
import typing

import pytest


class BaseError(Exception):
    """Base class for errors from this module."""


class NoEnabledPorts(BaseError):
    """Raised if there are not free ports for worker"""


def _is_port_free(port_num: int) -> bool:
    global socket_af
    socket_af = socket.AF_INET
    if hasattr(socket, 'AF_INET6'):
        socket_af = socket.AF_INET6

    sock = socket.socket(socket_af, socket.SOCK_STREAM)
    addr = ('127.0.0.1' if socket_af == socket.AF_INET else '::', port_num)
    try:
        sock.bind(addr)
        return True
    except OSError as err:
        if socket_af != socket.AF_INET and err.errno == errno.EADDRNOTAVAIL:
            socket_af = socket.AF_INET
            return _is_port_free(port_num)
    finally:
        sock.close()

    return False


@pytest.fixture(scope='session')
def get_free_port() -> typing.Callable[[], int]:
    """
    Returns an ephemeral TCP port that is free for IPv4 and for IPv6.
    """
    base_port = 30000
    last_port = 65000

    if platform.system() == 'Linux':
        range_fs = '/proc/sys/net/ipv4/ip_local_port_range'
        with open(range_fs) as range_file:
            data = range_file.read()
        new_base, new_last = data.strip().split()
        base_port = int(new_base)
        last_port = int(new_last)

    next_port = base_port

    def _get_free_port():
        nonlocal next_port

        while next_port <= last_port:
            next_port += 1

            if _is_port_free(next_port - 1):
                return next_port - 1

        raise NoEnabledPorts()

    return _get_free_port
