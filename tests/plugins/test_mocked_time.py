import datetime

import pytest

from testsuite.plugins import mocked_time as mocked_time_module


@pytest.mark.now('2020-01-01T00:00:00.000+0000')
def test_mocked_time_mutators(mocked_time):
    assert mocked_time.now() == datetime.datetime(2020, 1, 1, 0, 0, 0)

    mocked_time.sleep(1)
    assert mocked_time.now() == datetime.datetime(2020, 1, 1, 0, 0, 1)

    mocked_time.set(datetime.datetime(2021, 1, 1, 0, 0, 0))
    assert mocked_time.now() == datetime.datetime(2021, 1, 1, 0, 0, 0)


@pytest.mark.now(enabled=False)
def test_disabled_mocked_time_raises_on_usage_attempt(mocked_time):
    assert not mocked_time.is_enabled

    with pytest.raises(mocked_time_module.DisabledUsageError):
        mocked_time.set(datetime.datetime.utcnow())

    with pytest.raises(mocked_time_module.DisabledUsageError):
        mocked_time.sleep(2)
