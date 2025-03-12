import pytest

from testsuite import matching
from testsuite._internal import compare_transform


def test_basic():
    comparator = compare_transform.CompareTransform()
    right_mapped = comparator.visit(
        [4, 3, 2, 1],
        matching.unordered_list([1, 2, 4]),
    )

    assert right_mapped == [4, 2, 1]
    assert comparator.errors == {
        'left': [
            'dict length does not match len(left)=2, len(right)=3',
            "extra keys on the right: 'bar'",
        ]
    }
