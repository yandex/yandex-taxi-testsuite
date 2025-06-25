import pytest

from testsuite import compare_transform, matching


@pytest.mark.parametrize(
    'mode',
    (
        compare_transform.TransformMode.DEFAULT,
        compare_transform.TransformMode.EXPERIMENTAL,
    ),
)
def test_eq(mode):
    comparator = compare_transform.CompareTransform(
        mode, compare_transform.pytest_register_compare_transform_transformers()
    )
    mapped_left, mapped_right = comparator.compare_and_transform(
        ['foo', 'bar'],
        matching.ListOf(matching.any_string),
    )
    assert not comparator.errors
    assert mapped_right == ['foo', 'bar']


@pytest.mark.parametrize(
    'mode',
    (
        compare_transform.TransformMode.DEFAULT,
        compare_transform.TransformMode.EXPERIMENTAL,
    ),
)
def test_neq(mode):
    comparator = compare_transform.CompareTransform(
        mode, compare_transform.pytest_register_compare_transform_transformers()
    )
    mapped_left, mapped_right = comparator.compare_and_transform(
        ['foo', 'bar', 123],
        matching.ListOf(matching.any_string),
    )
    assert comparator.errors == {
        'left[2]': [
            '123 != <AnyString>',
        ],
    }
    assert mapped_right == ['foo', 'bar', matching.any_string]
