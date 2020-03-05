import datetime

import pytest
import pytz

from testsuite import utils

TZ_MOSCOW = pytz.timezone('Europe/Moscow')


@pytest.mark.parametrize(
    'stamp,result',
    [
        (
            datetime.datetime(2019, 1, 2, 11, 22, 33, 123132),
            datetime.datetime(2019, 1, 2, 11, 22, 33, 123132),
        ),
        (
            TZ_MOSCOW.localize(datetime.datetime(2019, 1, 2, 10, 30)),
            datetime.datetime(2019, 1, 2, 7, 30),
        ),
    ],
)
def test_to_utc(stamp, result):
    assert utils.to_utc(stamp) == result


@pytest.mark.parametrize(
    'stamp,result',
    [
        (
            datetime.datetime(2019, 1, 2, 11, 22, 33, 123132),
            '2019-01-02T11:22:33.123132+0000',
        ),
        (
            TZ_MOSCOW.localize(datetime.datetime(2019, 1, 2, 10, 30)),
            '2019-01-02T07:30:00.000000+0000',
        ),
    ],
)
def test_timestring(stamp, result):
    assert utils.timestring(stamp) == result
