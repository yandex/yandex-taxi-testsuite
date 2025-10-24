import pytest

from testsuite import compare_transform, matching


def test_basic(default_comparator):
    _, right_mapped = default_comparator.compare_and_transform(
        {'foo': 'bar', 'extra': 123},
        matching.PartialDict(foo='bar', bar=123),
    )

    assert right_mapped == {'foo': 'bar', 'bar': 123, 'extra': 123}
    assert default_comparator.errors == {
        'left': [
            'dict length does not match len(left)=2, len(right)=3',
            "extra keys on the right: 'bar'",
        ]
    }


def test_experimental(experimental_comparator):
    left_mapped, right_mapped = experimental_comparator.compare_and_transform(
        {'foo': 'bar', 'extra': 123},
        matching.PartialDict(foo='bar', bar=123),
    )

    assert left_mapped == {'foo': 'bar'}
    assert right_mapped == {'foo': 'bar', 'bar': 123}
    assert experimental_comparator.errors == {
        'left': [
            'dict length does not match len(left)=1, len(right)=2',
            "extra keys on the right: 'bar'",
        ]
    }


def test_match_error(parametrized_comparator):
    _, right = parametrized_comparator.compare_and_transform(
        matching.PartialDict(foo='bar', bar=123),
        123,
    )

    assert right == 123
    assert parametrized_comparator.errors == {
        'left': [
            "<PartialDict {'foo': 'bar', 'bar': 123}> != 123",
        ]
    }
