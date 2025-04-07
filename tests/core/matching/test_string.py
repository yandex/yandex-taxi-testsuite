import pytest

from testsuite import matching


def test_any_string():
    assert matching.any_string == 'foo'
    assert matching.any_string != b'foo'
    assert matching.any_string != 1


def test_regex_string():
    pred = matching.RegexString('^foo.*')
    assert pred == 'foo'
    assert pred == 'foobar'
    assert pred != 'fo'
    assert pred != 1


def test_uuid_string():
    assert matching.uuid_string == 'd08535a5904f4790bd8f95c51c1f3cbe'
    assert matching.uuid_string != 'foobar'


def test_objectid_string():
    assert matching.objectid_string == '5e64beab56d0bf70bd8eebbc'
    assert matching.objectid_string != 'foobar'


def test_datetime_string():
    assert matching.datetime_string == '2018-12-01'
    assert matching.datetime_string == '2018-12-01T14:00:01Z'
    assert matching.datetime_string == '2018-12-01T14:00:01+03:00'
    assert matching.datetime_string != 'foobar'


@pytest.mark.parametrize(
    ('left', 'right'),
    (
        (matching.any_string, matching.any_string),
        (matching.AnyString(), matching.AnyString()),
        (matching.RegexString('^foo.*'), matching.RegexString('^foo.*')),
        (matching.uuid_string, matching.uuid_string),
    ),
)
def test_instances(left, right):
    assert left == left
    assert right == right
    assert left == right
    assert right == left
