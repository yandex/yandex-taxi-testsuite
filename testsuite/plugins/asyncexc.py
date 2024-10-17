"""
Async exceptions handler.

Handle excpetions in background coroutines.
"""

import pytest


class BackgroundExceptionError(Exception):
    pass


@pytest.fixture
def _asyncexc():
    errors = []
    try:
        yield errors
    finally:
        __tracebackhide__ = True
        _raise_if_any(errors)


@pytest.fixture
def asyncexc_append(_asyncexc):
    """Register background exception."""
    return _asyncexc.append


@pytest.fixture
def asyncexc_check(_asyncexc):
    """Raise in case there are background exceptions."""

    def check():
        __tracebackhide__ = True
        _raise_if_any(_asyncexc)

    return check


def _raise_if_any(errors):
    if not errors:
        return
    errors = _clear_and_copy(errors)
    for exc in errors:
        __tracebackhide__ = True
        raise BackgroundExceptionError(
            f'There were {len(errors)} background exceptions'
            f', showing the first one',
        ) from exc


def _clear_and_copy(errors):
    copy = errors[:]
    errors.clear()
    return copy
