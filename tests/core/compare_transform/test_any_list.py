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
    left, right = comparator.visit([1, 2, 3], matching.AnyList())
    assert left == [1, 2, 3]
    assert right == [1, 2, 3]
    assert not comparator.errors


@pytest.mark.parametrize(
    'mode',
    (
        compare_transform.TransformMode.DEFAULT,
        compare_transform.TransformMode.EXPERIMENTAL,
    ),
)
def test_neq(mode):
    comparator = compare_transform.CompareTransform(
        mode, compare_transform.pytest_register_compare_transform_hooks()
    )
    left, right = comparator.visit({}, matching.AnyList())
    assert left == {}
    assert right == matching.AnyList()
    assert comparator.errors == {
        'left': ['dict expected on the right, got <AnyList> instead'],
    }


@pytest.mark.parametrize(
    'mode',
    (
        compare_transform.TransformMode.DEFAULT,
        compare_transform.TransformMode.EXPERIMENTAL,
    ),
)
def test_type_mismatch(mode):
    comparator = compare_transform.CompareTransform(
        mode, compare_transform.pytest_register_compare_transform_hooks()
    )
    comparator.visit(matching.AnyList(), {})
    assert comparator.errors == {
        'left': [
            '<AnyList> != {}',
        ],
    }
