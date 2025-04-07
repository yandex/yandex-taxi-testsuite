from testsuite import matching
from testsuite._internal import compare_transform


def test_neq():
    comparator = compare_transform.CompareTransform()
    left, right = comparator.visit(
        'foo',
        matching.Capture(matching.any_integer),
    )
    assert left == 'foo'
    assert right == matching.any_integer
    assert comparator.errors == {'left': ["'foo' != <IsInstance int>"]}


def test_neq_list_of():
    comparator = compare_transform.CompareTransform()
    left, right = comparator.visit(
        [1, 2, 3, 'foo'],
        matching.Capture(matching.ListOf(matching.any_integer)),
    )
    assert left == [1, 2, 3, 'foo']
    assert right == [1, 2, 3, matching.any_integer]
    assert comparator.errors == {
        'left[3]': [
            "'foo' != <IsInstance int>",
        ],
    }
