import pytest

from testsuite.plugins import assertrepr_compare

KEY_MAKER_KWARGS = {
    'dict_key_format': '[%r]',
    'dict_keys_connector': '',
    'sequence_key_format': '[%s]',
    'sequence_keys_connector': '',
}


class Foo:
    def __init__(self, val):
        self.val = val

    def __eq__(self, other):
        return self.val == other.val

    def __repr__(self):
        return 'Foo(%s)' % (self.val,)

    def __hash__(self):
        return hash(self.val)


@pytest.mark.nofilldb
@pytest.mark.parametrize(
    'left,right,expected',
    [
        (
            {
                'key_1': 1,
                'key_2': ['list_v_1', 'list_v_2'],
                'key_3': ['list_v_3', {'dict_in_list': 'v0'}],
                'key_4': ['list_v_1', 'list_v_2'],
                'key_5': {},
            },
            {
                'key_1': 11,
                'key_2': ['list_v_1', 'list_v_3', 'list_v_2'],
                'key_3': ['list_v_3.1', {'dict_in_list': 'v0', 'k1': 'v1'}],
                'key_4': ['list_v_1', 'list_v_2', 'list_v_4', 'list_v_3'],
                'key_6': {'dict_key': []},
                'key_7': {
                    'extra_big_dict_k1': {
                        'k0': {'\n\n'},
                        'k1': 'key\nvalue\n',
                    },
                    'extra_big_dict_k2': {
                        'k2': {'set'},
                        'k3\n': 'key\nvalue\n',
                        'k4': 'key\nvalue\n',
                    },
                },
            },
            [
                '',
                'Comparison failed (3):',
                ' * [\'key_1\']: 1 != 11',
                ' * [\'key_2\'][1]: \'list_v_2\' != \'list_v_3\'',
                ' * [\'key_3\'][0]: \'list_v_3\' != \'list_v_3.1\'',
                '',
                'Type mismatch (2):',
                ' * [\'key_2\']: '
                '<class \'list\'; length=2> != <class \'list\'; length=3>',
                ' * [\'key_4\']: '
                '<class \'list\'; length=2> != <class \'list\'; length=4>',
                '',
                'Extra fields in the left dict (1):',
                ' * [\'key_5\']: dict value: {}',
                '',
                'Extra fields in the right dict (6):',
                ' * [\'key_2\'][2]: list value: \'list_v_2\'',
                ' * [\'key_3\'][1][\'k1\']: dict value: \'v1\'',
                ' * [\'key_4\'][2]: list value: \'list_v_4\'',
                ' * [\'key_4\'][3]: list value: \'list_v_3\'',
                ' * [\'key_6\']: dict value: {\'dict_key\': []}',
                ' * [\'key_7\']: dict value:',
                '    {\'extra_big_dict_k1\': {\'k0\': {\'\\n\\n\'}, \'k1\': '
                '\'key\\nvalue\\n\'},',
                '     \'extra_big_dict_k2\': {\'k2\': {\'set\'},',
                '                           \'k3\\n\': \'key\\nvalue\\n\',',
                '                           \'k4\': \'key\\nvalue\\n\'}}',
            ],
        ),
        (
            {
                'key': [
                    'value',
                    {
                        'sub_key': {
                            'sub_value': [
                                1,
                                2,
                                3,
                                {
                                    'extra_set': {
                                        'set_v1',
                                        'set_v2',
                                        'set_v3',
                                    },
                                    'another_set': {},
                                },
                                {1, 2, 3, 'string', Foo('unsorted')},
                            ],
                        },
                    },
                ],
                'fail': range(10),
                'real': list(range(10)),
            },
            {
                'key': [
                    'value',
                    {
                        'sub_key': {
                            'sub_value': [
                                1,
                                2,
                                3,
                                {
                                    'extra_set': {
                                        'set_v1',
                                        'set_v2',
                                        'set_v3',
                                    },
                                    'another_set': {Foo('bar')},
                                },
                                {
                                    1,
                                    2,
                                    3,
                                    'string',
                                    Foo('unsorted'),
                                    Foo('extra_foo'),
                                    None,
                                },
                                [Foo('unsorted'), 1, 2, 'bar'],
                                None,
                            ],
                            'sub_value_2': ('world', 101010, 'hello'),
                        },
                    },
                ],
                'fail': range(6),
                'real': list(range(8)),
                'extra': None,
                Foo(''): 'foo_value',
                Foo(b''): 'b_foo_value',
            },
            [
                '',
                'Comparison failed (2):',
                ' * [\'fail\']: range(0, 10) != range(0, 6)',
                ' * [\'key\'][1][\'sub_key\'][\'sub_value\'][3]'
                '[\'another_set\']: {} != {Foo(bar)}',
                '',
                'Type mismatch (3):',
                ' * [\'key\'][1][\'sub_key\'][\'sub_value\']: '
                '<class \'list\'; length=5> != <class \'list\'; length=7>',
                ' * [\'key\'][1][\'sub_key\'][\'sub_value\'][3]'
                '[\'another_set\']: <class \'dict\'> != <class \'set\'>',
                ' * [\'real\']: '
                '<class \'list\'; length=10> != <class \'list\'; length=8>',
                '',
                'Extra fields in the left dict (2):',
                ' * [\'real\'][8]: list value: 8',
                ' * [\'real\'][9]: list value: 9',
                '',
                'Extra fields in the right dict (8):',
                ' * [Foo()]: dict value: \'foo_value\'',
                ' * [Foo(b\'\')]: dict value: \'b_foo_value\'',
                ' * [\'extra\']: dict value: None',
                ' * [\'key\'][1][\'sub_key\'][\'sub_value\'][4]: '
                'set value: Foo(extra_foo)',
                ' * [\'key\'][1][\'sub_key\'][\'sub_value\'][4]: '
                'set value: None',
                ' * [\'key\'][1][\'sub_key\'][\'sub_value\'][5]: '
                'list value: [Foo(unsorted), 1, 2, \'bar\']',
                ' * [\'key\'][1][\'sub_key\'][\'sub_value\'][6]: '
                'list value: None',
                ' * [\'key\'][1][\'sub_key\'][\'sub_value_2\']: '
                'dict value: (\'world\', 101010, \'hello\')',
            ],
        ),
        (
            {},
            {'': ''},
            [
                '',
                'Extra fields in the right dict (1):',
                ' * [\'\']: dict value: \'\'',
            ],
        ),
        (
            {},
            {1: '1', '1': 1, b'1': '1'},
            [
                '',
                'Extra fields in the right dict (3):',
                ' * [1]: dict value: \'1\'',
                ' * [\'1\']: dict value: 1',
                ' * [b\'1\']: dict value: \'1\'',
            ],
        ),
        (
            {'1': '1', 1: 1, b'1': b'1'},
            {1: '1', '1': 1, b'1': '1'},
            [
                '',
                'Comparison failed (3):',
                ' * [1]: 1 != \'1\'',
                ' * [\'1\']: \'1\' != 1',
                ' * [b\'1\']: b\'1\' != \'1\'',
                '',
                'Type mismatch (3):',
                ' * [1]: <class \'int\'> != <class \'str\'>',
                ' * [\'1\']: <class \'str\'> != <class \'int\'>',
                ' * [b\'1\']: <class \'bytes\'> != <class \'str\'>',
            ],
        ),
        (
            [1, 2, 3, (4, 5), {'6': 7}, 9],
            [1, 2, (3, 4), (5, 6), 7, {}, 9, 10],
            [
                '',
                'Comparison failed (5):',
                ' * [2]: 3 != (3, 4)',
                ' * [3][0]: 4 != 5',
                ' * [3][1]: 5 != 6',
                ' * [4]: {\'6\': 7} != 7',
                ' * [5]: 9 != {}',
                '',
                'Type mismatch (4):',
                ' * <class \'list\'; length=6> != <class \'list\'; length=8>',
                ' * [2]: <class \'int\'> != <class \'tuple\'>',
                ' * [4]: <class \'dict\'> != <class \'int\'>',
                ' * [5]: <class \'int\'> != <class \'dict\'>',
                '',
                'Extra fields in the right list (2):',
                ' * [6]: list value: 9',
                ' * [7]: list value: 10',
            ],
        ),
        (
            {'v': (1, 2, 3)},
            {'v': [1, 2, 3]},
            [
                '',
                'Comparison failed (1):',
                ' * [\'v\']: (1, 2, 3) != [1, 2, 3]',
                '',
                'Type mismatch (1):',
                ' * [\'v\']: <class \'tuple\'> != <class \'list\'>',
            ],
        ),
        (
            {'v': (1, 2, 3), 'v2': [1, 2]},
            {'v': [1, 2, 4], 'v2': [1, 2, 3]},
            [
                '',
                'Comparison failed (1):',
                ' * [\'v\']: (1, 2, 3) != [1, 2, 4]',
                '',
                'Type mismatch (2):',
                ' * [\'v\']: <class \'tuple\'> != <class \'list\'>',
                ' * [\'v2\']: '
                '<class \'list\'; length=2> != <class \'list\'; length=3>',
                '',
                'Extra fields in the right dict (1):',
                ' * [\'v2\'][2]: list value: 3',
            ],
        ),
        (
            {'v': frozenset([1])},
            {'v': frozenset(['1'])},
            [
                '',
                'Extra fields in the left dict (1):',
                ' * [\'v\']: frozenset value: 1',
                '',
                'Extra fields in the right dict (1):',
                ' * [\'v\']: frozenset value: \'1\'',
            ],
        ),
        (
            {'xx', 1, 2, 3, '232'},
            {1, 2, 4},
            [
                '',
                'Extra fields in the left set (3):',
                ' * set value: \'232\'',
                ' * set value: \'xx\'',
                ' * set value: 3',
                '',
                'Extra fields in the right set (1):',
                ' * set value: 4',
            ],
        ),
    ],
)
def test_compare_pair(left, right, expected):
    # pylint: disable=protected-access
    compare_result = assertrepr_compare._compare_pair(
        left,
        right,
        add_full_diff=False,
        depth=None,
        key_maker_kwargs=KEY_MAKER_KWARGS,
    )
    assert compare_result[1:] == expected
