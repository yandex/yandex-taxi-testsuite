from testsuite import compare_transform


def test_eq(default_comparator):
    default_comparator.compare_and_transform(['foo', 'bar'], ['foo', 'bar'])
    assert not default_comparator.errors


def test_type_mismatch(default_comparator):
    default_comparator.compare_and_transform([1, 2, 3], 1234)
    assert default_comparator.errors == {
        'left': ['list expected on the right got 1234 instead'],
    }


def test_extra_left(default_comparator):
    default_comparator.compare_and_transform(['foo', 'bar'], ['foo'])
    assert default_comparator.errors == {
        'left': [
            'list length does not match: len(left)=2 len(right)=1',
            "[1]: extra item on the left: 'bar'",
        ],
    }


def test_extra_right(default_comparator):
    default_comparator.compare_and_transform(['foo'], ['foo', 'bar'])
    assert default_comparator.errors == {
        'left': [
            'list length does not match: len(left)=1 len(right)=2',
            "[1]: extra item on the right: 'bar'",
        ],
    }
