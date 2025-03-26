from testsuite import matching
from testsuite._internal import compare_transform


def test_eq():
    comparator = compare_transform.CompareTransform()
    mapped_left, mapped_right = comparator.visit(
        ['foo', 'bar'],
        matching.ListOf(matching.any_string),
    )
    assert not comparator.errors
    assert mapped_right == ['foo', 'bar']


def test_neq():
    comparator = compare_transform.CompareTransform()
    mapped_left, mapped_right = comparator.visit(
        ['foo', 'bar', 123],
        matching.ListOf(matching.any_string),
    )
    assert comparator.errors == {
        'left[2]': [
            '123 != <AnyString>',
        ],
    }
    assert mapped_right == ['foo', 'bar', matching.any_string]
