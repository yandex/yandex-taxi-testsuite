import pytest

from testsuite import matching

PATTERN = matching.recursive_partial_dict(
    {'foo': {'bar': 123}, 'items': [{'x': 1}]},
)


@pytest.mark.parametrize(
    ('doc', 'pattern'),
    [
        (
            {
                'foo': {'bar': 123, 'extra': 123},
                'items': [{'x': 1, 'extra': 2}],
                'extra': 123,
            },
            PATTERN,
        ),
        (
            {'foo': {'bar': 123, 'extra': 1}},
            matching.recursive_partial_dict(
                {
                    'foo': matching.DictOf(
                        matching.any_string, matching.any_integer
                    ),
                }
            ),
        ),
        (
            {'items': [{'foo': 123, 'extra': 'xxx'}, {'foo': 321}]},
            matching.recursive_partial_dict(
                {
                    'items': matching.ListOf({'foo': matching.any_integer}),
                }
            ),
        ),
        (
            {'foo': {'extra': True}},
            matching.recursive_partial_dict(
                {
                    'foo': matching.Capture({}),
                }
            ),
        ),
    ],
)
def test_basic_eq(doc, pattern):
    assert doc == pattern


@pytest.mark.parametrize(
    ('doc', 'pattern'),
    [
        ({'fo1': {'bar': 123}, 'items': [{'x': 1}]}, PATTERN),
        ({'foo': {'bar': 124}, 'items': [{'x': 1}]}, PATTERN),
        ({'foo': {'bar': 124}, 'items': [{'x': 1}]}, PATTERN),
        ({'foo': {'bar': 123}, 'items': [{'x': 2}]}, PATTERN),
        (
            {'foo': {'bar': 'foo', 'extra': 1}},
            matching.recursive_partial_dict(
                {
                    'foo': matching.DictOf(
                        matching.any_string, matching.any_integer
                    ),
                }
            ),
        ),
        (
            {'items': [{'foo': 123, 'extra': 'xxx'}, {'foo': 'xxx'}]},
            matching.recursive_partial_dict(
                {
                    'items': matching.ListOf({'foo': matching.any_integer}),
                }
            ),
        ),
        (
            {'foo': {'bar': {'extra': 1}}},
            matching.recursive_partial_dict(
                {
                    'foo': matching.PartialDict({'bar': {}}),
                }
            ),
        ),
    ],
)
def test_basic_neq(doc, pattern):
    assert doc != pattern
