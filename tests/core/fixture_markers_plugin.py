import dataclasses

import pytest

from testsuite import fixture_markers


@dataclasses.dataclass(frozen=True)
class VisibilityMark:
    origin: str


def visibility(origin: str):
    def decorator(func):
        return fixture_markers.mark(func, VisibilityMark(origin=origin))

    return decorator


@pytest.fixture(scope='session')
@visibility('plugin')
def plugin_visibility():
    return 'plugin'
