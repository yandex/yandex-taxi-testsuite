import pytest

from testsuite import matching
from testsuite._internal import compare_transform


def test_basic():
    comparator = compare_transform.CompareTransform()
    _, right_mapped = comparator.visit(
        [4, 3, 2, 1],
        matching.unordered_list([1, 2, 4]),
    )

    assert right_mapped == [4, 2, 1]
    assert comparator.errors == {
        'left': [
            'list length does not match: len(left)=4 len(right)=3',
            '[3]: extra item on the left: 1',
        ],
        'left[1]': ['3 != 2'],
        'left[2]': ['2 != 1'],
    }


def test_experimental_basic():
    comparator = compare_transform.CompareTransform(
        compare_transform.TransformMode.EXPERIMENTAL
    )
    left_mapped, right_mapped = comparator.visit(
        [4, 3, 2, 1],
        matching.unordered_list([1, 2, 4]),
    )

    assert left_mapped == [1, 2, 3, 4]
    assert right_mapped == [1, 2, 4]

    assert comparator.errors == {
        'left': [
            'list length does not match: len(left)=4 len(right)=3',
            '[3]: extra item on the left: 4',
        ],
        'left[2]': ['3 != 4'],
    }


@pytest.mark.parametrize(
    'mode',
    (
        compare_transform.TransformMode.DEFAULT,
        compare_transform.TransformMode.EXPERIMENTAL,
    ),
)
def test_match_error(mode):
    comparator = compare_transform.CompareTransform(mode)
    comparator.visit(
        matching.unordered_list([1, 2, 4]),
        42,
    )
    assert comparator.errors == {
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
def test_order_restore(left, right, expected):
    comparator = compare_transform.CompareTransform()
    _, right_mapped = comparator.visit(
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
def test_order_restore_experimental(left, right, expected):
    comparator = compare_transform.CompareTransform(
        compare_transform.TransformMode.EXPERIMENTAL
    )
    left_mapped, righ_mapped = comparator.visit(
        left,
        right,
    )

    assert left_mapped == expected
    assert righ_mapped == right._value


def test_same_key():
    comparator = compare_transform.CompareTransform()
    _, right_mapped = comparator.visit(
        [0], matching.unordered_list([1], key=lambda x: 1)
    )
    assert right_mapped == [1]
