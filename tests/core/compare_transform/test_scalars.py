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
def test_eq(left, right):
    comparator = compare_transform.CompareTransform(
        compare_transform.TransformMode.DEFAULT,
        compare_transform.pytest_register_compare_transform_transformers(),
    )
    comparator.compare_and_transform(left, right)
    assert not comparator.errors


def test_neq():
    comparator = compare_transform.CompareTransform(
        compare_transform.TransformMode.DEFAULT,
        compare_transform.pytest_register_compare_transform_transformers(),
    )
    comparator.compare_and_transform(1, 2)
    assert comparator.errors == {
        'left': [
            '1 != 2',
        ]
    }
