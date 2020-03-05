import os
import socket

DOCKERTEST_WORKER = os.getenv('DOCKERTEST_WORKER', '')


class BaseError(Exception):
    pass


class RootUserForbiddenError(BaseError):
    pass


def test_tcp_connection(host: str, port: int, timeout: float = 1) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def ensure_non_root_user():
    if not os.getenv('TESTSUITE_ALLOW_ROOT') and os.getuid() == 0:
        raise RootUserForbiddenError('Running testsuite as root is forbidden')
