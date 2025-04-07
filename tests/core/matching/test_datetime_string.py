from testsuite import matching


def test_repr():
    assert repr(matching.datetime_string) == '<DatetimeString>'


def test_datetime_string():
    assert matching.datetime_string == '2018-12-01'
    assert matching.datetime_string == '2018-12-01T14:00:01Z'
    assert matching.datetime_string == '2018-12-01T14:00:01+03:00'
    assert matching.datetime_string != 'foobar'
    assert matching.datetime_string != 1234


def test_equality():
    assert matching.datetime_string == matching.datetime_string
