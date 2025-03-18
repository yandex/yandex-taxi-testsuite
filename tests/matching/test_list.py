from testsuite.utils import matching


def test_repr():
    assert repr(matching.any_list) == '<AnyList>'
    assert repr(matching.ListOf()) == '<ListOf value=<Any>>'


def test_any_list():
    assert matching.any_list == []
    assert matching.any_list == ['foo', 'bar']
    assert matching.any_list != {}


def test_list():
    pred = matching.ListOf(matching.any_string)
    assert pred != 123
    assert pred == ['foo', 'bar']
    assert pred != ['foo', 1]

    assert matching.ListOf(matching.any_string) == matching.ListOf(
        matching.any_string
    )
    assert matching.ListOf(matching.any_string) != matching.ListOf(
        matching.any_integer
    )
