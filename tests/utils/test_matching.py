from testsuite.utils import matching


def test_anystring():
    assert matching.any_string == 'foo'
    assert matching.any_string != b'foo'
    assert matching.any_string != 1


def test_regex_string():
    pred = matching.RegexString('^foo.*')
    assert pred == 'foo'
    assert pred == 'foobar'
    assert pred != 'fo'
    assert pred != 1


def test_uuid_string():
    assert matching.uuid_string == 'd08535a5904f4790bd8f95c51c1f3cbe'
    assert matching.uuid_string != 'foobar'


def test_objectid_string():
    assert matching.objectid_string == '5e64beab56d0bf70bd8eebbc'
    assert matching.objectid_string != 'foobar'


def test_datetime_string():
    assert matching.datetime_string == '2018-12-01'
    assert matching.datetime_string == '2018-12-01T14:00:01Z'
    assert matching.datetime_string == '2018-12-01T14:00:01+03:00'
    assert matching.datetime_string != 'foobar'


def test_any_float():
    assert matching.any_float == 1.0
    assert matching.any_float != 1
    assert matching.any_float != 'foo'


def test_any_integer():
    assert matching.any_integer == 1
    assert matching.any_integer != 1.0
    assert matching.any_integer != 'foo'


def test_any_numeric():
    assert matching.any_numeric == 1
    assert matching.any_numeric == 1.0
    assert matching.any_numeric != 'foo'


def test_positive_float():
    assert matching.positive_float != 0.0
    assert matching.positive_float == 1.0
    assert matching.positive_float != -1.0
    assert matching.positive_float != 'foo'


def test_positive_integer():
    assert matching.positive_integer != 0
    assert matching.positive_integer == 1
    assert matching.positive_integer != -1
    assert matching.positive_integer != 'foo'


def test_positive_numeric():
    assert matching.positive_numeric != 0.0
    assert matching.positive_numeric == 1.0
    assert matching.positive_numeric != -1.0
    assert matching.positive_numeric != 0
    assert matching.positive_numeric == 1
    assert matching.positive_numeric != -1
    assert matching.positive_numeric != 'foo'


def test_negative_float():
    assert matching.negative_float != 0.0
    assert matching.negative_float != 1.0
    assert matching.negative_float == -1.0
    assert matching.negative_float != 'foo'


def test_negative_integer():
    assert matching.negative_integer != 0
    assert matching.negative_integer != 1
    assert matching.negative_integer == -1
    assert matching.negative_integer != 'foo'


def test_negative_numeric():
    assert matching.negative_numeric != 0.0
    assert matching.negative_numeric != 1.0
    assert matching.negative_numeric == -1.0
    assert matching.negative_numeric != 0
    assert matching.negative_numeric != 1
    assert matching.negative_numeric == -1
    assert matching.negative_numeric != 'foo'


def test_non_negative_float():
    assert matching.non_negative_float == 0.0
    assert matching.non_negative_float == 1.0
    assert matching.non_negative_float != -1.0
    assert matching.non_negative_float != 'foo'


def test_non_negative_integer():
    assert matching.non_negative_integer == 0
    assert matching.non_negative_integer == 1
    assert matching.non_negative_integer != -1
    assert matching.non_negative_integer != 'foo'


def test_non_negative_numeric():
    assert matching.non_negative_numeric == 0.0
    assert matching.non_negative_numeric == 1.0
    assert matching.non_negative_numeric != -1.0
    assert matching.non_negative_numeric == 0
    assert matching.non_negative_numeric == 1
    assert matching.non_negative_numeric != -1
    assert matching.non_negative_numeric != 'foo'


def test_gt():
    assert matching.Gt(0) != 0
    assert matching.Gt(0) == 1
    assert matching.Gt(0) != -1
    assert matching.Gt(0) != 'foo'


def test_ge():
    assert matching.Ge(0) == 0
    assert matching.Ge(0) == 1
    assert matching.Ge(0) != -1
    assert matching.Ge(0) != 'foo'


def test_lt():
    assert matching.Lt(0) != 0
    assert matching.Lt(0) != 1
    assert matching.Lt(0) == -1
    assert matching.Lt(0) != 'foo'


def test_le():
    assert matching.Le(0) == 0
    assert matching.Le(0) != 1
    assert matching.Le(0) == -1
    assert matching.Le(0) != 'foo'


def test_or():
    assert matching.Or(1, 2) == 1
    assert matching.Or(1, 2) == 2
    assert matching.Or(1, 2) != 3
    assert matching.Or(1, 2) != 'foo'


def test_and():
    assert matching.And(matching.Ge(10), matching.Le(20)) == 10
    assert matching.And(matching.Ge(10), matching.Le(20)) == 15
    assert matching.And(matching.Ge(10), matching.Le(20)) == 20
    assert matching.And(matching.Ge(10), matching.Le(20)) != 21
    assert matching.And(matching.Ge(10), matching.Le(20)) != 9
    assert matching.And(matching.Ge(10), matching.Le(20)) != 'foo'


def test_not():
    assert matching.Not(3) == 2
    assert matching.Not(3) != 3
    assert matching.Not(3) == 'foo'


def test_partial_dict():
    sample = {
        'some_int': 1,
        'some_str': 'abc',
        'some_dict': {'a': 5, 'b': 'b', 'c': 6},
    }

    assert sample == matching.PartialDict(some_int=1)
    assert sample == matching.PartialDict(some_int=1, some_str='abc')
    assert sample == matching.PartialDict(
        some_int=1,
        some_str='abc',
        some_dict=matching.PartialDict(a=5),
    )

    assert sample != matching.PartialDict(some_int=2)
    assert sample != matching.PartialDict(unknown=3)
    assert sample != matching.PartialDict(
        some_int=1,
        some_str='abc',
        some_dict=matching.PartialDict(a=123, asd=55),
    )

    assert matching.PartialDict() != 5

    assert sample == matching.PartialDict({'some_int': 1})

    assert sample == matching.PartialDict(some_int=1)
    assert not (sample != matching.PartialDict(some_int=1))


def test_unordered_list():
    assert [1, 3, 2] == matching.unordered_list([3, 2, 1])
    assert [{'v': 'a'}, {'v': 'b'}] == matching.unordered_list(
        [{'v': 'b'}, {'v': 'a'}], key=lambda x: x['v']
    )


def test_recursive_partial_dict():
    sample = {
        'some_key': 'some_value',
        'some_map_like_object': [('a', 1), ('b', 2), ('c', 3)],
        'some_dict': {
            'wrapped_int': 10_000,
            'wrapped_str': 'value',
            'wrapped_dict': {
                'inner_key': 'inner_value',
                'inner_dict': {
                    'other_key': 'other_value',
                },
            },
        },
    }

    needle = {'some_key': 'some_value'}
    assert sample == matching.RecursivePartialDict(**needle)
    needle = {'some_map_like_object': [('a', 1), ('b', 2), ('c', 3)]}
    assert sample == matching.RecursivePartialDict(**needle)
    needle = {'some_dict': {}}
    assert sample == matching.RecursivePartialDict(**needle)
    needle = {'some_dict': {'wrapped_int': 10_000}}
    assert sample == matching.RecursivePartialDict(**needle)
    needle = {'some_dict': {'wrapped_str': 'value'}}
    assert sample == matching.RecursivePartialDict(**needle)
    needle = {'some_dict': {'wrapped_dict': {}}}
    assert sample == matching.RecursivePartialDict(**needle)
    needle = {'some_dict': {'wrapped_dict': {'inner_key': 'inner_value'}}}
    assert sample == matching.RecursivePartialDict(**needle)
    needle = {'some_dict': {'wrapped_dict': {'inner_dict': {}}}}
    assert sample == matching.RecursivePartialDict(**needle)
    
    needle = {'some_map_like_object': {'a': 1, 'b': 2, 'c': 3}}
    assert sample != matching.RecursivePartialDict(**needle)
