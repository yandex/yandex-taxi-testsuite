import pytest

from testsuite import compare_transform, matching


@pytest.mark.parametrize(
    ('left', 'right'),
    [
        # object
        (object(), matching.any_value),
        # strings
        ('foo', 'foo'),
        ('foo', matching.any_value),
        ('foo', matching.any_string),
        # integers
        (123, matching.any_integer),
        (123, matching.Ge(100)),
        (matching.Ge(100), 123),
        # lists
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, 3], matching.any_list),
        ([1, 2, 3], matching.ListOf(matching.any_integer)),
        # dicts
        ({'foo': 'bar'}, {'foo': 'bar'}),
        ({'foo': 'bar'}, matching.any_dict),
        (
            {'foo': 'bar'},
            matching.DictOf(matching.any_string, matching.any_string),
        ),
        ({'foo': 'bar', 'bar': 123}, matching.PartialDict({'foo': 'bar'})),
        # tuples
        ((1, 2, 3), (1, 2, 3)),
        # sets
        ({1, 2, 3}, {1, 2, 3}),
    ],
)
def test_eq(left, right, default_comparator):
    # compare left and right
    _, mapped_right = default_comparator.compare_and_transform(left, right)
    assert not default_comparator.errors
    assert left == _, mapped_right

    # compare right and left
    _, mapped_left = default_comparator.compare_and_transform(right, left)
    assert not default_comparator.errors
    assert mapped_left == right

    # compare left and left
    _, mapped_left = default_comparator.compare_and_transform(left, left)
    assert not default_comparator.errors
    assert mapped_left == left

    # compare right and right
    _, mapped_right = default_comparator.compare_and_transform(right, right)
    assert not default_comparator.errors
    assert _, mapped_right == right
