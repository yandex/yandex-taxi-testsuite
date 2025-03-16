import asyncio
import warnings

import pytest

from . import warnings as asyncio_warnings


def pytest_configure(config):
    # Force default asyncio mode
    config.option.asyncio_mode = 'auto'
    # Force fixtures to use session loop
    config.inicfg['asyncio_default_fixture_loop_scope'] = 'session'


def pytest_collection_modifyitems(items):
    """Force tests to use session asyncio loop."""
    for item in items:
        mark = item.get_closest_marker('asyncio')
        if mark:
            mark.kwargs.setdefault('loop_scope', 'session')


@pytest.fixture(scope='session')
async def event_loop():
    warnings.warn(
        asyncio_warnings.LOOP_DEPRECATION_MESSAGE,
        pytest.PytestDeprecationWarning,
    )
    return asyncio.get_running_loop()


@pytest.fixture(scope='session')
def loop(event_loop):
    return event_loop
