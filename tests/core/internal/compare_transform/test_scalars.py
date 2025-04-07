import pytest

from testsuite import matching
from testsuite._internal import compare_transform


@pytest.mark.parametrize(
    ('left', 'right'),
    [
        (1, 1),
        (1, matching.any_value),
        (1, matching.any_integer),
    ],
)
def test_eq(left, right):
    comparator = compare_transform.CompareTransform()
    comparator.visit(left, right)
    assert not comparator.errors


def test_neq():
    comparator = compare_transform.CompareTransform()
    comparator.visit(1, 2)
    assert comparator.errors == {
        'left': [
            '1 != 2',
        ]
    }
