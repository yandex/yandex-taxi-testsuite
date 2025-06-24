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
        mode, compare_transform.pytest_register_compare_transform_hooks()
    )
    mapped_left, mapped_right = comparator.visit(
        {'foo': 'bar'},
        matching.DictOf(matching.any_string, matching.any_string),
    )
    assert not comparator.errors
    assert mapped_right == {'foo': 'bar'}


@pytest.mark.parametrize(
    'mode',
    (
        compare_transform.TransformMode.DEFAULT,
        compare_transform.TransformMode.EXPERIMENTAL,
    ),
)
def test_value_nq(mode):
    comparator = compare_transform.CompareTransform(
        mode, compare_transform.pytest_register_compare_transform_hooks()
    )
    comparator.visit(
        {'foo': 'bar'},
        matching.DictOf(matching.any_string, matching.any_integer),
    )
    assert comparator.errors == {"left['foo']": ["'bar' != <IsInstance int>"]}


@pytest.mark.parametrize(
    'mode',
    (
        compare_transform.TransformMode.DEFAULT,
        compare_transform.TransformMode.EXPERIMENTAL,
    ),
)
def test_value_nq_reversed(mode):
    comparator = compare_transform.CompareTransform(
        compare_transform.TransformMode.DEFAULT,
        compare_transform.pytest_register_compare_transform_hooks(),
    )
    left_mapped, right_mapped = comparator.visit(
        matching.DictOf(matching.any_string, matching.any_integer),
        {'foo': 'bar'},
    )
    left_mapped = {'foo': matching.any_integer}
    right_mapped = {'foo': 'bar'}
    assert comparator.errors == {"left['foo']": ["<IsInstance int> != 'bar'"]}


@pytest.mark.parametrize(
    'mode',
    (
        compare_transform.TransformMode.DEFAULT,
        compare_transform.TransformMode.EXPERIMENTAL,
    ),
)
def test_key_nq(mode):
    comparator = compare_transform.CompareTransform(
        mode, compare_transform.pytest_register_compare_transform_hooks()
    )

    comparator.visit(
        {'foo': 'bar'},
        matching.DictOf(matching.any_integer, matching.any_string),
    )
    assert comparator.errors == {
        "left['foo']": ['dict key must match <IsInstance int> expression']
    }
