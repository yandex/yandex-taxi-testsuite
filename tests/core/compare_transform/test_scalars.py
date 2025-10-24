import pytest

from testsuite import compare_transform, matching


@pytest.mark.parametrize(
    ('left', 'right'),
    [
        (1, 1),
        (1, matching.any_value),
        (1, matching.any_integer),
    ],
)
def test_eq(left, right, parametrized_comparator):
    parametrized_comparator.compare_and_transform(left, right)
    assert not parametrized_comparator.errors


def test_neq(parametrized_comparator):
    parametrized_comparator.compare_and_transform(1, 2)
    assert parametrized_comparator.errors == {
        'left': [
            '1 != 2',
        ]
    }
