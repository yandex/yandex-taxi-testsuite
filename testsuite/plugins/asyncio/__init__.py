import asyncio
import warnings

import pytest_aiohttp
from packaging import version

PYTEST_ASYNCIO_VERSION = version.parse('0.22')

LOOP_DEPRECATION_MESSAGE = """\
Testsuite fixtures `event_loop` and `loop` are deprecated.

Tests and fixtures should use "asyncio.get_running_loop()" instead.
Please use `async def` for tests and fixtures that are meant to run in asyncio event_loop."""


def _pytest_asyncio_legacy():
    try:
        import pytest_asyncio
    except ImportError:
        return True
    return version.parse(pytest_asyncio.__version__) < PYTEST_ASYNCIO_VERSION


# type: ignore
if _pytest_asyncio_legacy():
    from .plugin_legacy import *
else:
    from .plugin import *


@pytest.fixture(scope='session')
async def loop(event_loop):
    warnings.warn(
        LOOP_DEPRECATION_MESSAGE,
        pytest.PytestDeprecationWarning,
    )
    return asyncio.get_running_loop()
