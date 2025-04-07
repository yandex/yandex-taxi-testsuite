from testsuite._internal import compare_transform


def test_eq():
    comparator = compare_transform.CompareTransform()
    comparator.visit(['foo', 'bar'], ['foo', 'bar'])
    assert not comparator.errors


def test_type_mismatch():
    comparator = compare_transform.CompareTransform()
    comparator.visit([1, 2, 3], 1234)
    assert comparator.errors == {
        'left': ['list expected on the right got 1234 instead'],
    }


def test_extra_left():
    comparator = compare_transform.CompareTransform()
    comparator.visit(['foo', 'bar'], ['foo'])
    assert comparator.errors == {
        'left': [
            'list length does not match: len(left)=2 len(right)=1',
            "[1]: extra item on the left: 'bar'",
        ],
    }


def test_extra_right():
    comparator = compare_transform.CompareTransform()
    comparator.visit(['foo'], ['foo', 'bar'])
    assert comparator.errors == {
        'left': [
            'list length does not match: len(left)=1 len(right)=2',
            "[1]: extra item on the right: 'bar'",
        ],
    }
