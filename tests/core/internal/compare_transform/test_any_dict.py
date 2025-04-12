import pytest

from testsuite import matching
from testsuite._internal import compare_transform


@pytest.mark.parametrize(
    'mode',
    (
        compare_transform.TransformMode.DEFAULT,
        compare_transform.TransformMode.EXPERIMENTAL,
    ),
)
def test_eq(mode):
    comparator = compare_transform.CompareTransform(mode)
    left, right = comparator.visit({'foo': 'bar'}, matching.AnyDict())
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
    comparator = compare_transform.CompareTransform(mode)
    left, right = comparator.visit(matching.AnyDict(), 123)
    assert left == matching.AnyDict()
    assert right == 123
    assert comparator.errors == {
        'left': [
            '<AnyDict> != 123',
        ],
    }
