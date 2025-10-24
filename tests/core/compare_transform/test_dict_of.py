import pytest

from testsuite import compare_transform, matching


def test_eq(parametrized_comparator):
    mapped_left, mapped_right = parametrized_comparator.compare_and_transform(
        {'foo': 'bar'},
        matching.DictOf(matching.any_string, matching.any_string),
    )
    assert not parametrized_comparator.errors
    assert mapped_right == {'foo': 'bar'}


def test_value_nq(parametrized_comparator):
    parametrized_comparator.compare_and_transform(
        {'foo': 'bar'},
        matching.DictOf(matching.any_string, matching.any_integer),
    )
    assert parametrized_comparator.errors == {
        "left['foo']": ["'bar' != <IsInstance int>"]
    }


def test_value_nq_reversed(parametrized_comparator):
    left_mapped, right_mapped = parametrized_comparator.compare_and_transform(
        matching.DictOf(matching.any_string, matching.any_integer),
        {'foo': 'bar'},
    )
    left_mapped = {'foo': matching.any_integer}
    right_mapped = {'foo': 'bar'}
    assert parametrized_comparator.errors == {
        "left['foo']": ["<IsInstance int> != 'bar'"]
    }


def test_key_nq(parametrized_comparator):
    parametrized_comparator.compare_and_transform(
        {'foo': 'bar'},
        matching.DictOf(matching.any_integer, matching.any_string),
    )
    assert parametrized_comparator.errors == {
        "left['foo']": ['dict key must match <IsInstance int> expression']
    }
