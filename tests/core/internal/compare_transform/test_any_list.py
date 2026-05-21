from testsuite import matching
from testsuite._internal import compare_transform


def test_eq():
    comparator = compare_transform.CompareTransform()
    left, right = comparator.visit([1, 2, 3], matching.AnyList())
    assert left == [1, 2, 3]
    assert right == [1, 2, 3]
    assert not comparator.errors


def test_neq():
    comparator = compare_transform.CompareTransform()
    left, right = comparator.visit({}, matching.AnyList())
    assert left == {}
    assert right == matching.AnyList()
    assert comparator.errors == {
        'left': ['dict expected on the right, got <AnyList> instead'],
    }


def test_type_mismatch():
    comparator = compare_transform.CompareTransform()
    comparator.visit(matching.AnyList(), {})
    assert comparator.errors == {
        'left': [
            '<AnyList> != {}',
        ],
    }
