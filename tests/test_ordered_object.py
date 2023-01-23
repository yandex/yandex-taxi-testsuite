import copy

import pytest

from testsuite.utils import ordered_object


@pytest.mark.parametrize(
    'test_obj1, test_obj2, expected_obj, paths',
    [
        (
            {
                'key1': 'value1',
                'set1': [
                    {
                        'key2': {'key3': 'value3'},
                        'set2': ['string3', 'string1', 'string2'],
                    },
                    {
                        'key4': 'value4',
                        'set2': ['string2', 'string3', 'string1'],
                    },
                ],
            },
            {
                'key1': 'value1',
                'set1': [
                    {
                        'key4': 'value4',
                        'set2': ['string2', 'string1', 'string3'],
                    },
                    {
                        'set2': ['string3', 'string2', 'string1'],
                        'key2': {'key3': 'value3'},
                    },
                ],
            },
            {
                'key1': 'value1',
                'set1': [
                    {
                        'key2': {'key3': 'value3'},
                        'set2': ['string1', 'string2', 'string3'],
                    },
                    {
                        'key4': 'value4',
                        'set2': ['string1', 'string2', 'string3'],
                    },
                ],
            },
            ['set1', 'set1.set2'],
        ),
        (
            {
                'key1': 'value1',
                'set1': ({'key2': 'value2'}, {'key3': 'value3'}),
            },
            {
                'key1': 'value1',
                'set1': ({'key3': 'value3'}, {'key2': 'value2'}),
            },
            {
                'key1': 'value1',
                'set1': [{'key2': 'value2'}, {'key3': 'value3'}],
            },
            ['set1'],
        ),
        (
            {
                'key1': 'value1',
                'set1': [
                    'string1',
                    1,
                    'string2',
                    {'key3': 'value3', 'key2': 'value2', 'key4': 'value4'},
                    {'set2': [1, '1']},
                ],
            },
            {
                'set1': [
                    'string2',
                    {'key4': 'value4', 'key3': 'value3', 'key2': 'value2'},
                    'string1',
                    {'set2': [1, '1']},
                    1,
                ],
                'key1': 'value1',
            },
            {
                'key1': 'value1',
                'set1': [
                    {'key2': 'value2', 'key3': 'value3', 'key4': 'value4'},
                    {'set2': [1, '1']},
                    1,
                    'string1',
                    'string2',
                ],
            },
            ['set1'],
        ),
        (['c', 'b', 'a'], ['b', 'c', 'a'], ['a', 'b', 'c'], ['']),
    ],
)
def test_ordered_object(test_obj1, test_obj2, expected_obj, paths):
    copy_obj1 = copy.deepcopy(test_obj1)
    assert ordered_object.order(test_obj1, paths) == expected_obj
    assert copy_obj1 == test_obj1

    copy_obj2 = copy.deepcopy(test_obj2)
    assert ordered_object.order(test_obj2, paths) == expected_obj
    assert copy_obj2 == test_obj2

    ordered_object.assert_eq(test_obj1, test_obj2, paths)


def test_non_list_value_is_silently_skipped():
    # foo.bar points to numeric values 2 which cannot be sorted
    result = ordered_object.order(
        {'foo': [{'bar': 2}, {'bar': [3, 1, 2]}]},
        ['foo.bar'],
    )
    assert result == {'foo': [{'bar': 2}, {'bar': [1, 2, 3]}]}
