import pytest

from testsuite import compare_transform, matching


def test_basic():
    comparator = compare_transform.CompareTransform(
        compare_transform.TransformMode.DEFAULT,
        compare_transform.pytest_register_compare_transform_transformers(),
    )
    _, right_mapped = comparator.compare_and_transform(
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


def test_experimental():
    comparator = compare_transform.CompareTransform(
        compare_transform.TransformMode.EXPERIMENTAL,
        compare_transform.pytest_register_compare_transform_transformers(),
    )
    left_mapped, right_mapped = comparator.compare_and_transform(
        {'foo': 'bar', 'extra': 123},
        matching.PartialDict(foo='bar', bar=123),
    )

    assert left_mapped == {'foo': 'bar'}
    assert right_mapped == {'foo': 'bar', 'bar': 123}
    assert comparator.errors == {
        'left': [
            'dict length does not match len(left)=1, len(right)=2',
            "extra keys on the right: 'bar'",
        ]
    }


@pytest.mark.parametrize(
    'mode',
    (
        compare_transform.TransformMode.DEFAULT,
        compare_transform.TransformMode.EXPERIMENTAL,
    ),
)
def test_match_error(mode):
    comparator = compare_transform.CompareTransform(
        mode, compare_transform.pytest_register_compare_transform_transformers()
    )
    _, right = comparator.compare_and_transform(
        matching.PartialDict(foo='bar', bar=123),
        123,
    )

    assert right == 123
    assert comparator.errors == {
        'left': [
            "<PartialDict {'foo': 'bar', 'bar': 123}> != 123",
        ]
    }
