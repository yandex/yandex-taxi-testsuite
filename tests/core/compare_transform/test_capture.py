from testsuite import compare_transform, matching


def test_neq():
    comparator = compare_transform.CompareTransform(
        compare_transform.TransformMode.DEFAULT,
        compare_transform.pytest_register_compare_transform_hooks(),
    )
    left, right = comparator.visit(
        'foo',
        matching.Capture(matching.any_integer),
    )
    assert left == 'foo'
    assert right == matching.any_integer
    assert comparator.errors == {'left': ["'foo' != <IsInstance int>"]}


def test_neq_list_of():
    comparator = compare_transform.CompareTransform(
        compare_transform.TransformMode.DEFAULT,
        compare_transform.pytest_register_compare_transform_hooks(),
    )
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
