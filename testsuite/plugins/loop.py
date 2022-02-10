import asyncio

import pytest
import uvloop


@pytest.fixture(scope='session')
def loop():
    """
    One event loop for all tests.
    """
    event_loop = uvloop.new_event_loop()
    asyncio.set_event_loop(event_loop)
    try:
        yield event_loop
    finally:
        event_loop.close()


@pytest.fixture(scope='session')
def event_loop(loop):
    return loop
