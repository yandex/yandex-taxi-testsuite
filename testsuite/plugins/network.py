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


@pytest.fixture(scope='session')
def _get_ipv6_af_or_fallback():
    if not hasattr(socket, 'AF_INET6'):
        return socket.AF_INET

    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    try:
        sock.bind(('::', 0))
        return socket.AF_INET6
    finally:
        sock.close()

    return socket.AF_INET


@pytest.fixture(scope='session')
def _get_ipv6_localhost_or_fallback(_get_ipv6_af_or_fallback):
    if _get_ipv6_af_or_fallback == socket.AF_INET:
        return '127.0.0.1'

    return '::'


def _is_port_free(port_num: int, socket_af, host: str) -> bool:
    sock = socket.socket(socket_af, socket.SOCK_STREAM)
    try:
        sock.bind((host, port_num))
        return True
    finally:
        sock.close()

    return False


@pytest.fixture(scope='session')
async def _get_open_sock_list_impl():
    sock_list = set()
    try:
        yield sock_list
    finally:
        for sock in sock_list:
            sock.close()


def _get_free_port_sock_storing(
    socket_af,
    host: str,
    sock_list: set,
) -> typing.Callable[[], int]:
    # Relies on https://github.com/torvalds/linux/commit/aacd9289af8b82f5fb01b
    def _get_free_port():
        nonlocal sock_list

        sock = socket.socket(socket_af, socket.SOCK_STREAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, 0))
            sock_list.add(sock)
            return sock.getsockname()[1]
        except OSError:
            raise NoEnabledPorts()


async def _get_free_port_range_based(
    socket_af,
    host: str,
) -> typing.Callable[[], int]:
    port = 61000

    def _get_free_port():
        nonlocal port

        close_to_privileged_ports = 2048
        while port > close_to_privileged_ports:
            port -= 1

            if _is_port_free(port, socket_af, host):
                return port

        raise NoEnabledPorts()

    return _get_free_port


@pytest.fixture(scope='session')
def get_free_port(
    _get_ipv6_af_or_fallback,
    _get_ipv6_localhost_or_fallback,
    _get_open_sock_list_impl,
) -> typing.Callable[[], int]:
    """
    Returns an ephemeral TCP port that is free for IPv4 and for IPv6.
    """
    if platform.system() == 'Linux':
        return _get_free_port_sock_storing(
            _get_ipv6_af_or_fallback,
            _get_ipv6_localhost_or_fallback,
            _get_open_sock_list_impl,
        )

    return _get_free_port_range_based(
        _get_ipv6_af_or_fallback,
        _get_ipv6_localhost_or_fallback,
    )
