from testsuite._internal import compare_transform


def test_value_neq():
    comparator = compare_transform.CompareTransform()
    comparator.visit({'foo': 'bar'}, {'foo': 123})
    assert comparator.errors == {'left["foo"]': ["'bar' != 123"]}


def test_length_neq():
    comparator = compare_transform.CompareTransform()
    comparator.visit({'foo': 'bar'}, {'foo': 'bar', 'bar': 123})
    assert comparator.errors == {
        'left': [
            'dict length does not match len(left)=1, len(right)=2',
            "extra keys on the right: 'bar'",
        ]
    }


def test_type_neq():
    comparator = compare_transform.CompareTransform()
    comparator.visit({'foo': 'bar'}, 123)
    assert comparator.errors == {
        'left': ["dict expected on the right, got <class 'int'> instead"]
    }


def test_extra_keys():
    comparator = compare_transform.CompareTransform()
    comparator.visit({'foo': 'bar'}, {'bar': 'foo'})
    assert comparator.errors == {
        'left': [
            "extra keys on the left: 'foo'",
            "extra keys on the right: 'bar'",
        ],
    }
