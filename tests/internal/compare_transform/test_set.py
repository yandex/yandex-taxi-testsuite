from testsuite._internal import compare_transform


def test_eq():
    comparator = compare_transform.CompareTransform()
    comparator.visit({'foo', 'bar'}, {'foo', 'bar'})
    assert not comparator.errors


def test_type_mismatch():
    comparator = compare_transform.CompareTransform()
    comparator.visit({'foo', 'bar', 'maurice'}, 1234)
    assert comparator.errors == {
        'left': ['type mismatch, set expected got: 1234']
    }


def test_extra_left():
    comparator = compare_transform.CompareTransform()
    comparator.visit({'foo', 'bar', 'maurice'}, {'foo', 'bar'})
    assert comparator.errors == {'left': ["extra items on the left: 'maurice'"]}


def test_extra_right():
    comparator = compare_transform.CompareTransform()
    comparator.visit({'foo', 'bar'}, {'foo', 'bar', 'maurice'})
    assert comparator.errors == {
        'left': ["extra items on the right: 'maurice'"]
    }
