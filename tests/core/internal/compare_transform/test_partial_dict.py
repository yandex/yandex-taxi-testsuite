from testsuite import matching
from testsuite._internal import compare_transform


def test_basic():
    comparator = compare_transform.CompareTransform()
    _, right_mapped = comparator.visit(
        {'foo': 'bar', 'extra': 123},
        matching.PartialDict(foo='bar', bar=123),
    )

    assert right_mapped == {'foo': 'bar', 'bar': 123, 'extra': 123}
    assert comparator.errors == {
        'left': [
            'dict length does not match len(left)=2, len(right)=3',
            "extra keys on the right: 'bar'",
        ]
    }


def test_match_error():
    comparator = compare_transform.CompareTransform()
    _, right = comparator.visit(
        matching.PartialDict(foo='bar', bar=123),
        123,
    )

    assert right == 123
    assert comparator.errors == {
        'left': [
            "<PartialDict {'foo': 'bar', 'bar': 123}> != 123",
        ]
    }
