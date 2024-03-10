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


def _get_ipv6_localhost_or_fallback() -> str:
    if not hasattr(socket, 'AF_INET6'):
        return socket.AF_INET

    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        sock.bind(('::', 0))
        return socket.AF_INET6
    finally:
        sock.close()

    return socket.AF_INET


_IPV6_AF_OR_FALLBACK = _get_ipv6_localhost_or_fallback()
_LOCALHOST = ('127.0.0.1' if _IPV6_AF_OR_FALLBACK == socket.AF_INET else '::')


def _is_port_free(port_num: int) -> bool:
    sock = socket.socket(_IPV6_AF_OR_FALLBACK, socket.SOCK_STREAM)
    try:
        sock.bind((_LOCALHOST, port_num))
        return True
    finally:
        sock.close()

    return False


def _get_free_port_sock_storing() -> typing.Callable[[], int]:
    # Relies on https://github.com/torvalds/linux/commit/aacd9289af8b82f5fb01b
    sock_list = set()

    def _get_free_port():
        nonlocal sock_list

        sock = socket.socket(_IPV6_AF_OR_FALLBACK, socket.SOCK_STREAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((_LOCALHOST, 0))
            sock_list.add(sock)
            return sock.getsockname()[1]
        except OSError as err:
            raise NoEnabledPorts()

    try:
        yield _get_free_port
    finally:
        for sock in sock_list:
            sock.close()


def _get_free_port_range_based() -> typing.Callable[[], int]:
    base_port = 30000
    last_port = 65000
    next_port = base_port

    def _get_free_port():
        nonlocal next_port

        while next_port <= last_port:
            next_port += 1

            if _is_port_free(next_port - 1):
                return next_port - 1

        raise NoEnabledPorts()

    return _get_free_port


@pytest.fixture(scope='session')
def get_free_port() -> typing.Callable[[], int]:
    """
    Returns an ephemeral TCP port that is free for IPv4 and for IPv6.

    Provides strong guarantee that no other application could bind
    to that port via bind(('', 0)).
    """
    if platform.system() == 'Linux':
        return _get_free_port_sock_storing()
    else:
        return _get_free_port_range_based()
