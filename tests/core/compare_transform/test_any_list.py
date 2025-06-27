import pytest

from testsuite import compare_transform, matching


def test_eq(parametrized_comparator):
    left, right = parametrized_comparator.compare_and_transform(
        [1, 2, 3], matching.AnyList()
    )
    assert left == [1, 2, 3]
    assert right == [1, 2, 3]
    assert not parametrized_comparator.errors


def test_neq(parametrized_comparator):
    left, right = parametrized_comparator.compare_and_transform(
        {}, matching.AnyList()
    )
    assert left == {}
    assert right == matching.AnyList()
    assert parametrized_comparator.errors == {
        'left': ['dict expected on the right, got <AnyList> instead'],
    }


def test_type_mismatch(parametrized_comparator):
    parametrized_comparator.compare_and_transform(matching.AnyList(), {})
    assert parametrized_comparator.errors == {
        'left': [
            '<AnyList> != {}',
        ],
    }
