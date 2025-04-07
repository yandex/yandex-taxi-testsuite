from testsuite import matching
from testsuite._internal import compare_transform


def test_eq():
    comparator = compare_transform.CompareTransform()
    left, right = comparator.visit({'foo': 'bar'}, matching.AnyDict())
    assert left == {'foo': 'bar'}
    assert right == {'foo': 'bar'}
    assert not comparator.errors


def test_neq():
    comparator = compare_transform.CompareTransform()
    left, right = comparator.visit(matching.AnyDict(), 123)
    assert left == matching.AnyDict()
    assert right == 123
    assert comparator.errors == {
        'left': [
            '<AnyDict> != 123',
        ],
    }
