import datetime

import dateutil.parser
import pytest

from testsuite import utils


class MockedTime:
    def __init__(self, time):
        self._now = time

    def sleep(self, delta: float):
        self._now += datetime.timedelta(seconds=delta)

    def now(self):
        return self._now

    def set(self, time):
        self._now = time


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'now: specify current time mocked value',
    )


@pytest.fixture
def mocked_time(now):
    return MockedTime(now)


@pytest.fixture
def now(request):
    marker = request.node.get_closest_marker('now')
    if not marker:
        return datetime.datetime.utcnow()
    stamp = marker.args[0]
    if isinstance(stamp, int):
        return datetime.datetime.utcfromtimestamp(stamp)
    return utils.to_utc(dateutil.parser.parse(stamp))
