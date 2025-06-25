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
    left, right = comparator.compare_and_transform(
        {'foo': 'bar'}, matching.AnyDict()
    )
    assert left == {'foo': 'bar'}
    assert right == {'foo': 'bar'}
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
        mode, compare_transform.pytest_register_compare_transform_transformers()
    )
    left, right = comparator.compare_and_transform(matching.AnyDict(), 123)
    assert left == matching.AnyDict()
    assert right == 123
    assert comparator.errors == {
        'left': [
            '<AnyDict> != 123',
        ],
    }
