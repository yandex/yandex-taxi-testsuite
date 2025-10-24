from testsuite import compare_transform, matching


def test_neq(default_comparator):
    left, right = default_comparator.compare_and_transform(
        'foo',
        matching.Capture(matching.any_integer),
    )
    assert left == 'foo'
    assert right == matching.any_integer
    assert default_comparator.errors == {'left': ["'foo' != <IsInstance int>"]}


def test_neq_list_of(default_comparator):
    left, right = default_comparator.compare_and_transform(
        [1, 2, 3, 'foo'],
        matching.Capture(matching.ListOf(matching.any_integer)),
    )
    assert left == [1, 2, 3, 'foo']
    assert right == [1, 2, 3, matching.any_integer]
    assert default_comparator.errors == {
        'left[3]': [
            "'foo' != <IsInstance int>",
        ],
    }
