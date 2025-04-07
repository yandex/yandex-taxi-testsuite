from testsuite import matching


def test_repr():
    assert repr(matching.any_dict) == '<AnyDict>'
    assert repr(matching.DictOf()) == '<DictOf key=<Any> value=<Any>>'


def test_any_dict():
    assert matching.any_dict == {}
    assert matching.any_dict == {'foo': 'bar'}
    assert matching.any_dict != []


def test_dict():
    pred = matching.DictOf(value=matching.any_string)
    assert pred == {'foo': 'bar'}
    assert pred != {'foo': 1}
    assert 123 != pred

    pred = matching.DictOf(key=matching.any_string)
    assert pred == {'foo': 'bar'}
    assert pred != {1: 'bar'}


def test_visit():
    pred = matching.DictOf(matching.any_integer, matching.any_string)

    visited = []

    def visitor(value):
        visited.append(value)
        return value

    copy = pred.__testsuite_visit__(visitor)

    assert visited == [matching.any_integer, matching.any_string]

    assert copy == pred
