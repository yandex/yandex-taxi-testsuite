from testsuite.utils import matching


def test_any_list():
    assert matching.any_list == []
    assert matching.any_list == ['foo', 'bar']
    assert matching.any_list != {}


def test_list():
    pred = matching.ListOf(matching.any_string)
    assert pred == ['foo', 'bar']
    assert pred != ['foo', 1]
