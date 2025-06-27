import pytest

from testsuite import compare_transform, matching


def test_eq(parametrized_comparator):
    mapped_left, mapped_right = parametrized_comparator.compare_and_transform(
        ['foo', 'bar'],
        matching.ListOf(matching.any_string),
    )
    assert not parametrized_comparator.errors
    assert mapped_right == ['foo', 'bar']


def test_neq(parametrized_comparator):
    mapped_left, mapped_right = parametrized_comparator.compare_and_transform(
        ['foo', 'bar', 123],
        matching.ListOf(matching.any_string),
    )
    assert parametrized_comparator.errors == {
        'left[2]': [
            '123 != <AnyString>',
        ],
    }
    assert mapped_right == ['foo', 'bar', matching.any_string]
