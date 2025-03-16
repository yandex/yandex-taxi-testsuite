import asyncio
import contextlib
import warnings

import pytest

from . import warnings as asyncio_warnings


def pytest_configure(config):
    # Force default asyncio mode
    config.option.asyncio_mode = 'auto'


@pytest.fixture(scope='session')
def event_loop():
    """
    One event loop for all tests.
    """
    warnings.warn(
        asyncio_warnings.LOOP_DEPRECATION_MESSAGE,
        pytest.PytestDeprecationWarning,
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop


@pytest.fixture(scope='session')
def loop(event_loop):
    return event_loop
