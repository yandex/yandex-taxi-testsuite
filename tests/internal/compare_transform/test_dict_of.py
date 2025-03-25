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


def test_value_nq():
    comparator = compare_transform.CompareTransform()
    comparator.visit(
        {'foo': 'bar'},
        matching.DictOf(matching.any_string, matching.any_integer),
    )
    assert comparator.errors == {'left["foo"]': ["'bar' != <IsInstance int>"]}


def test_value_nq_reversed():
    comparator = compare_transform.CompareTransform()
    left_mapped, right_mapped = comparator.visit(
        matching.DictOf(matching.any_string, matching.any_integer),
        {'foo': 'bar'},
    )
    left_mapped = {'foo': matching.any_integer}
    right_mapped = {'foo': 'bar'}
    assert comparator.errors == {'left["foo"]': ["<IsInstance int> != 'bar'"]}


def test_key_nq():
    comparator = compare_transform.CompareTransform()

    comparator.visit(
        {'foo': 'bar'},
        matching.DictOf(matching.any_integer, matching.any_string),
    )
    assert comparator.errors == {
        'left': ["'foo': dict keys must match <IsInstance int> expression"]
    }
