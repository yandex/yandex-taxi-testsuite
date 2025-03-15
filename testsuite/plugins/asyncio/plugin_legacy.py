import asyncio
import contextlib

import pytest


def pytest_configure(config):
    # Force default asyncio mode
    config.option.asyncio_mode = 'auto'


@pytest.fixture(scope='session')
def event_loop():
    """
    One event loop for all tests.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with contextlib.closing(loop):
        yield loop


@pytest.fixture(scope='session')
def loop(event_loop):
    return event_loop
