from testsuite import compare_transform


def test_value_neq(default_comparator):
    default_comparator.compare_and_transform({'foo': 'bar'}, {'foo': 123})
    assert default_comparator.errors == {"left['foo']": ["'bar' != 123"]}


def test_length_neq(default_comparator):
    default_comparator.compare_and_transform(
        {'foo': 'bar'}, {'foo': 'bar', 'bar': 123}
    )
    assert default_comparator.errors == {
        'left': [
            'dict length does not match len(left)=1, len(right)=2',
            "extra keys on the right: 'bar'",
        ]
    }


def test_type_neq(default_comparator):
    default_comparator.compare_and_transform({'foo': 'bar'}, 123)
    assert default_comparator.errors == {
        'left': ['dict expected on the right, got 123 instead']
    }


def test_extra_keys(default_comparator):
    default_comparator.compare_and_transform({'foo': 'bar'}, {'bar': 'foo'})
    assert default_comparator.errors == {
        'left': [
            "extra keys on the left: 'foo'",
            "extra keys on the right: 'bar'",
        ],
    }
