import pytest

from testsuite import compare_transform, matching


def test_basic(default_comparator):
    _, right_mapped = default_comparator.compare_and_transform(
        [4, 3, 2, 1],
        matching.unordered_list([1, 2, 4]),
    )

    assert right_mapped == [4, 2, 1]
    assert default_comparator.errors == {
        'left': [
            'list length does not match: len(left)=4 len(right)=3',
            '[3]: extra item on the left: 1',
        ],
        'left[1]': ['3 != 2'],
        'left[2]': ['2 != 1'],
    }


def test_experimental_basic(experimental_comparator):
    left_mapped, right_mapped = experimental_comparator.compare_and_transform(
        [4, 3, 2, 1],
        matching.unordered_list([1, 2, 4]),
    )

    assert left_mapped == [1, 2, 3, 4]
    assert right_mapped == [1, 2, 4]

    assert experimental_comparator.errors == {
        'left': [
            'list length does not match: len(left)=4 len(right)=3',
            '[3]: extra item on the left: 4',
        ],
        'left[2]': ['3 != 4'],
    }


def test_match_error(parametrized_comparator):
    parametrized_comparator.compare_and_transform(
        matching.unordered_list([1, 2, 4]),
        42,
    )
    assert parametrized_comparator.errors == {
        'left': [
            '<UnorderedList: [1, 2, 4]> != 42',
        ],
    }


@pytest.mark.parametrize(
    ('left', 'right', 'expected'),
    [
        ([3, 2, 1], matching.unordered_list([1, 2, 4, 5, 6]), [2, 1, 4, 5, 6]),
        ([3, 2, 1], matching.unordered_list([1, 2]), [2, 1]),
        ([3, 2, 1], matching.unordered_list([0, 1]), [1, 0]),
        ([3, 2, 1], matching.unordered_list([0]), [0]),
    ],
)
def test_order_restore(default_comparator, left, right, expected):
    _, right_mapped = default_comparator.compare_and_transform(
        left,
        right,
    )

    assert right_mapped == expected


@pytest.mark.parametrize(
    ('left', 'right', 'expected'),
    [
        ([3, 2, 1], matching.unordered_list([1, 2, 4, 5, 6]), [1, 2, 3]),
        ([3, 2, 1], matching.unordered_list([1, 2]), [1, 2, 3]),
        ([3, 2, 1], matching.unordered_list([0, 1]), [1, 2, 3]),
        ([3, 2, 1], matching.unordered_list([0]), [1, 2, 3]),
    ],
)
def test_order_restore_experimental(
    experimental_comparator, left, right, expected
):
    left_mapped, righ_mapped = experimental_comparator.compare_and_transform(
        left,
        right,
    )

    assert left_mapped == expected
    assert righ_mapped == right._value


def test_same_key(default_comparator):
    _, right_mapped = default_comparator.compare_and_transform(
        [0], matching.unordered_list([1], key=lambda x: 1)
    )
    assert right_mapped == [1]
