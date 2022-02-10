import contextlib
import itertools
import socket
import typing

import pytest

BASE_PORT = 30000
MAX_PORTS_NUMBER = 100


class BaseError(Exception):
    """Base class for errors from this module."""


class NoEnabledPorts(BaseError):
    """Raised if there are not free ports for worker"""


@pytest.fixture(scope='session')
def get_free_port(worker_id: str) -> typing.Callable[[], int]:
    counter = itertools.islice(itertools.count(), MAX_PORTS_NUMBER)
    worker_num = 0 if worker_id == 'master' else int(worker_id[2:]) + 1

    def _get_free_port():
        for value in counter:
            port = BASE_PORT + worker_num * MAX_PORTS_NUMBER + value
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            with contextlib.closing(sock):
                result_code = sock.connect_ex(('localhost', port))
            if result_code != 0:
                return port
        raise NoEnabledPorts()

    return _get_free_port
