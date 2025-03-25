from testsuite import matching
from testsuite._internal import compare_transform


def test_eq():
    comparator = compare_transform.CompareTransform()
    mapped_left, mapped_right = comparator.visit(
        {'foo': 'bar'},
        matching.DictOf(matching.any_string, matching.any_string),
    )
    assert not comparator.errors
    assert mapped_right == {'foo': 'bar'}


def test_reversed():
    comparator = compare_transform.CompareTransform()
    mapped_left, mapped_right = comparator.visit(
        matching.DictOf(matching.any_string, matching.any_string),
        {'foo': 'bar'},
    )
    assert not comparator.errors
    assert mapped_left == {'foo': 'bar'}
    assert mapped_right == {'foo': 'bar'}


def test_value_nq():
    comparator = compare_transform.CompareTransform()
    comparator.visit(
        {'foo': 'bar'},
        matching.DictOf(matching.any_string, matching.any_integer),
    )
    assert comparator.errors == {'left["foo"]': ["'bar' != <IsInstance int>"]}


def test_key_nq():
    comparator = compare_transform.CompareTransform()

    comparator.visit(
        {'foo': 'bar'},
        matching.DictOf(matching.any_integer, matching.any_string),
    )
    assert comparator.errors == {
        'left': ["'foo': dict keys must match <IsInstance int> expression"]
    }
