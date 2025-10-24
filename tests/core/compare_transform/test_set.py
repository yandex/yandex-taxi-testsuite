from testsuite import compare_transform


def test_eq(default_comparator):
    default_comparator.compare_and_transform({'foo', 'bar'}, {'foo', 'bar'})
    assert not default_comparator.errors


def test_type_mismatch(default_comparator):
    default_comparator.compare_and_transform({'foo', 'bar', 'maurice'}, 1234)
    assert default_comparator.errors == {
        'left': ['set expected on the right got 1234 instead'],
    }


def test_extra_left(default_comparator):
    default_comparator.compare_and_transform(
        {'foo', 'bar', 'maurice'}, {'foo', 'bar'}
    )
    assert default_comparator.errors == {
        'left': ["extra items on the left: 'maurice'"],
    }


def test_extra_right(default_comparator):
    default_comparator.compare_and_transform(
        {'foo', 'bar'}, {'foo', 'bar', 'maurice'}
    )
    assert default_comparator.errors == {
        'left': ["extra items on the right: 'maurice'"],
    }


def test_mapping_set(default_comparator):
    left, right = default_comparator.compare_and_transform(
        {'foo', 'bar'}, {'foo', 'bar', 'maurice'}
    )
    assert left == {'foo', 'bar'}
    assert right == {'foo', 'bar', 'maurice'}
    assert default_comparator.errors == {
        'left': ["extra items on the right: 'maurice'"],
    }


def test_mapping_frozenset(default_comparator):
    left, right = default_comparator.compare_and_transform(
        frozenset(['foo', 'bar']), {'foo', 'bar', 'maurice'}
    )
    assert left == {'foo', 'bar'}
    assert right == {'foo', 'bar', 'maurice'}
    assert default_comparator.errors == {
        'left': ["extra items on the right: 'maurice'"],
    }
