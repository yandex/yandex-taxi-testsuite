from testsuite.utils import matching


def test_any_dict():
    assert matching.any_dict == {}
    assert matching.any_dict == {'foo': 'bar'}
    assert matching.any_dict != []


def test_dict():
    pred = matching.DictOf(value=matching.any_string)
    assert pred == {'foo': 'bar'}
    assert pred != {'foo': 1}

    pred = matching.DictOf(key=matching.any_string)
    assert pred == {'foo': 'bar'}
    assert pred != {1: 'bar'}
