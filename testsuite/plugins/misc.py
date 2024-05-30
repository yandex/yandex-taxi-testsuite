import contextlib


def pytest_sessionstart():
    # Ignore contextlib tracebacks
    contextlib.__tracebackhide__ = True


def pytest_sessionfinish():
    del contextlib.__tracebackhide__
