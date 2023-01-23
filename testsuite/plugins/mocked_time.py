import datetime

import dateutil.parser
import pytest

from testsuite import utils

MOCK_TIME_DISABLED_MESSAGE = (
    'Mock time is disabled. Use @pytest.mark.now to enable mock '
    'time for a particular test'
)


class BaseError(Exception):
    """Base class for errors in this module"""


class DisabledUsageError(BaseError):
    """Raised when attempting to use a disabled feature"""


class MockedTime:
    def __init__(self, time: datetime.datetime, *, is_enabled: bool):
        self._now = time
        self._is_enabled = is_enabled

    def sleep(self, delta: float) -> None:
        """Increase mock time value

        :param delta: increase value in seconds
        """
        if not self._is_enabled:
            raise DisabledUsageError(MOCK_TIME_DISABLED_MESSAGE)
        self._now += datetime.timedelta(seconds=delta)

    def now(self) -> datetime.datetime:
        """:returns: current value of mock time"""
        if self._is_enabled:
            return self._now
        return datetime.datetime.utcnow()

    def set(self, time: datetime.datetime):
        """Set mock time value"""
        if not self._is_enabled:
            raise DisabledUsageError(MOCK_TIME_DISABLED_MESSAGE)
        self._now = time

    @property
    def is_enabled(self) -> bool:
        return self._is_enabled


def pytest_addoption(parser):
    parser.addini(
        name='mocked-time-enabled',
        type='bool',
        default=True,
        help='Set false to disable mocked time by default',
    )


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'now: specify current time mocked value',
    )


def pytest_register_object_hooks():
    return {
        '$dateDiff': {'$fixture': '_date_diff_hook'},
        '$timeDelta': _time_delta_hook,
    }


def pytest_servicetest_modifyitem(session, item):
    item.add_marker(pytest.mark.now(enabled=False))


@pytest.fixture
def mocked_time(_mocked_time_enabled, now) -> MockedTime:
    """:returns: :py:class:`MockedTime`"""
    return MockedTime(now, is_enabled=_mocked_time_enabled)


@pytest.fixture
def now(request) -> datetime.datetime:
    marker = request.node.get_closest_marker('now')
    if not marker or not marker.args:
        return datetime.datetime.utcnow()
    stamp = marker.args[0]
    if isinstance(stamp, int):
        return datetime.datetime.utcfromtimestamp(stamp)
    return utils.to_utc(dateutil.parser.parse(stamp))


@pytest.fixture
def _mocked_time_enabled(request, pytestconfig) -> bool:
    now_marker_exists = False
    for marker in request.node.iter_markers(name='now'):
        if 'enabled' in marker.kwargs:
            return marker.kwargs['enabled']
        now_marker_exists = True
    if now_marker_exists:
        return True
    return pytestconfig.getini('mocked-time-enabled')


@pytest.fixture
def _date_diff_hook(now):
    def wrapper(doc: dict):
        seconds = float(doc['$dateDiff'])
        return now + datetime.timedelta(seconds=seconds)

    return wrapper


def _time_delta_hook(doc: dict):
    delta = float(doc['$timeDelta'])
    return datetime.timedelta(seconds=delta)
