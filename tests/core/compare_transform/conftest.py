import pytest

from testsuite import compare_transform


@pytest.fixture
def default_comparator() -> compare_transform.CompareTransform:
    return compare_transform.CompareTransform(
        compare_transform.TransformMode.DEFAULT,
        compare_transform.default_transformers(),
    )


@pytest.fixture
def experimental_comparator() -> compare_transform.CompareTransform:
    return compare_transform.CompareTransform(
        compare_transform.TransformMode.EXPERIMENTAL,
        compare_transform.default_transformers(),
    )


@pytest.fixture(params=['experimental', 'default'])
def parametrized_comparator(
    request, default_comparator, experimental_comparator
) -> compare_transform.CompareTransform:
    return (
        default_comparator
        if request.param == 'default'
        else experimental_comparator
    )
