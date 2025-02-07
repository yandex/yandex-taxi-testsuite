from testsuite.utils import json_util


def test_default_datetime_tzinfo(now):
    assert json_util.default(now) == now
