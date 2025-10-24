import pytest

from testsuite import compare_transform, matching


def test_eq(parametrized_comparator):
    left, right = parametrized_comparator.compare_and_transform(
        {'foo': 'bar'}, matching.AnyDict()
    )
    assert left == {'foo': 'bar'}
    assert right == {'foo': 'bar'}
    assert not parametrized_comparator.errors


def test_neq(parametrized_comparator):
    left, right = parametrized_comparator.compare_and_transform(
        matching.AnyDict(), 123
    )
    assert left == matching.AnyDict()
    assert right == 123
    assert parametrized_comparator.errors == {
        'left': [
            '<AnyDict> != 123',
        ],
    }
