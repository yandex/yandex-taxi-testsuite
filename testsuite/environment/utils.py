import os
import socket
import typing

DOCKERTEST_WORKER = os.getenv('DOCKERTEST_WORKER', '')


class BaseError(Exception):
    pass


class RootUserForbiddenError(BaseError):
    pass


class EnvironmentVariableError(BaseError):
    pass


def test_tcp_connection(host: str, port: int, timeout: float = 1) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def ensure_non_root_user() -> None:
    if not os.getenv('TESTSUITE_ALLOW_ROOT') and os.getuid() == 0:
        raise RootUserForbiddenError('Running testsuite as root is forbidden')


def getenv_int(key: str, default: int) -> int:
    env_value = os.getenv(key)
    if env_value is None:
        return default
    try:
        result = int(env_value)
    except ValueError as err:
        raise EnvironmentVariableError(
            f'{key} environment variable is expected to have integer value. '
            f'Actual value: {env_value}',
        ) from err
    else:
        return result


def getenv_ints(
        key: str, default: typing.Tuple[int, ...],
) -> typing.Tuple[int, ...]:
    env_value = os.getenv(key, None)
    if env_value is None:
        return default
    try:
        result = tuple(int(value) for value in env_value.split(','))
    except ValueError as err:
        raise EnvironmentVariableError(
            f'{key} environment variable is expected to be a comma-separated '
            f'list of integers. Actual value: {env_value}',
        ) from err
    else:
        return result
