import collections
import copy
import operator
import pprint
import typing

import py.io

from testsuite.utils import matching

# pylint: disable=unidiomatic-typecheck

CMP_SIMPLE_DIFF = 0
CMP_INCONSISTENCY_TYPES = 1
CMP_EXTRA_LEFT = 2
CMP_EXTRA_RIGHT = 3

GROUP_DESC_FMT = {
    CMP_INCONSISTENCY_TYPES: 'Type mismatch (%(count)d):',
    CMP_SIMPLE_DIFF: 'Comparison failed (%(count)d):',
    CMP_EXTRA_LEFT: 'Extra fields in the left %(type)s (%(count)d):',
    CMP_EXTRA_RIGHT: 'Extra fields in the right %(type)s (%(count)d):',
}

NOT_A_KEY = object()

CmpInfo = collections.namedtuple(
    'CmpInfo', ['cmp_type', 'left_value', 'right_value', 'parent_type'],
)

SEQUENCE_TYPES: tuple = (list, tuple)
SET_TYPES: tuple = (set, frozenset)
TYPES = (dict,) + SET_TYPES + SEQUENCE_TYPES


class ReprKeyMaker:
    def __init__(
            self,
            dict_key_format='[%r]',
            dict_keys_connector='',
            sequence_key_format='[%s]',
            sequence_keys_connector='',
    ):
        self.dict_key_format = dict_key_format
        self.dict_keys_connector = dict_keys_connector
        self.sequence_key_format = sequence_key_format
        self.sequence_keys_connector = sequence_keys_connector

    def make(self, key):
        parts = []
        for sub_key in key:
            if isinstance(sub_key, int):
                connector = self.sequence_keys_connector
                formatter = self.sequence_key_format
            else:
                connector = self.dict_keys_connector
                formatter = self.dict_key_format
            if parts:
                parts.append(connector)
            parts.append(formatter % (sub_key,))
        if not parts:
            return NOT_A_KEY
        return ''.join(parts)


class Comparator:
    def __init__(self, depth=None):
        self.depth = depth

    def compare(self, left, right):
        return self._compare(left, right, level=0)

    def _compare(self, left, right, level):
        type_left = _match_type(left)
        type_right = _match_type(right)
        same_types = type_left is type_right
        different_sequence_lengths = (
            type_left in SEQUENCE_TYPES
            and type_right in SEQUENCE_TYPES
            and len(left) != len(right)
        )
        if (not same_types or different_sequence_lengths) and (
                left is not None and right is not None
        ):
            left_type_info = type_left
            right_type_info = type_right
            if different_sequence_lengths:
                left_type_info = _make_length_info(left)
                right_type_info = _make_length_info(right)
            yield (), CmpInfo(
                CMP_INCONSISTENCY_TYPES, left_type_info, right_type_info, None,
            )
        if (
                not same_types
                or type_left not in TYPES
                or (self.depth is not None and level >= self.depth)
        ):
            if left != right:
                yield (), CmpInfo(CMP_SIMPLE_DIFF, left, right, None)
            return

        parent_type = type_left
        is_set = isinstance(left, SET_TYPES)
        if isinstance(left, SEQUENCE_TYPES):
            keys = range(max(len(left), len(right)))
            left = dict(enumerate(left))
            right = dict(enumerate(right))
        else:
            if is_set:
                left = {key: key for key in left}
                right = {key: key for key in right}
            keys = set(list(left.keys()) + list(right.keys()))

        for key in keys:
            path_sub_key = () if is_set else (key,)
            if key not in left:
                yield (
                    path_sub_key,
                    CmpInfo(CMP_EXTRA_RIGHT, None, right[key], parent_type),
                )
            elif key not in right:
                yield (
                    path_sub_key,
                    CmpInfo(CMP_EXTRA_LEFT, left[key], None, parent_type),
                )
            elif left[key] != right[key]:
                for path, cmp_info in self._compare(
                        left[key], right[key], level=level + 1,
                ):
                    yield (*path_sub_key, *path), cmp_info


def pytest_addoption(parser):
    """
    :param parser: pytest's argument parser
    """
    group = parser.getgroup('common')
    group.addoption(
        '--assert-mode',
        choices=['default', 'combine', 'analyze'],
        default='combine',
        help='Assertion representation mode, combined by default',
    )
    group.addoption(
        '--assert-depth',
        type=int,
        default=None,
        help='Depth of assertions, use 0 for simple print different items',
    )


# pylint: disable=invalid-name
def pytest_assertrepr_compare(config, op, left, right):
    assertion_mode = config.option.assert_mode
    if (
            # pylint: disable=unidiomatic-typecheck
            assertion_mode == 'default'
            or op != '=='
            or type(left) is not type(right)
            or type(left) not in TYPES
    ):
        return None
    add_full_diff = assertion_mode == 'combine'
    add_empty_lines = config.option.verbose > 1
    return _compare_pair(
        left,
        right,
        add_empty_lines=add_empty_lines,
        add_full_diff=add_full_diff,
        depth=config.option.assert_depth,
    )


def _compare_pair(
        left,
        right,
        add_empty_lines=True,
        add_full_diff=False,
        depth=None,
        records_limit=None,
        key_maker_kwargs=None,
        repr_func=None,
) -> typing.List[str]:
    def _group_by_type(cmp_result):
        total_records = 0
        default_dict = {'parts': [], 'extra_count': 0}
        groups = collections.defaultdict(lambda: copy.deepcopy(default_dict))
        records_limit_exceeded = False
        for key, failed_cmp_info, repr_lines in cmp_result:
            cmp_type = failed_cmp_info.cmp_type
            if records_limit is not None and total_records >= records_limit:
                records_limit_exceeded = True
            parts = groups[cmp_type]['parts']
            if not records_limit_exceeded or not parts:
                parts.append((key, repr_lines))
                total_records += 1
            else:
                groups[cmp_type]['extra_count'] += 1
        return groups

    def _to_explanations(cmp_results_by_type) -> typing.List[typing.List[str]]:
        key_maker = ReprKeyMaker(**(key_maker_kwargs or {}))
        groups = []
        for cmp_type, to_repr in sorted(
                cmp_results_by_type.items(), key=operator.itemgetter(0),
        ):
            parts = to_repr['parts']
            extra_count = to_repr['extra_count']
            group_desc = GROUP_DESC_FMT[cmp_type] % {
                'count': len(parts) + extra_count,
                'type': type(left).__name__,
            }
            group = [group_desc]
            for key, repr_lines in parts:
                repr_key = key_maker.make(key)
                part_lines = _format_cmp_part(repr_key, repr_lines)
                group.extend(part_lines)
            if extra_count:
                group.append(' ...and %d extra problems' % extra_count)
            groups.append(group)
        return groups

    if type(left) is not type(right) or type(left) not in TYPES:
        raise ValueError(
            'Incorrect input types: %s, %s' % (type(left), type(right)),
        )
    if left == right:
        raise ValueError('Input equal! %s == %s' % (left, right))
    if repr_func is None:
        repr_func = pprint.pformat

    comparator = Comparator(depth=depth)
    repr_cmp_result = sorted(
        [
            (
                key,
                failed_cmp_info,
                _make_repr_lines(failed_cmp_info, repr_func),
            )
            for key, failed_cmp_info in comparator.compare(left, right)
        ],
        key=_cmp_sort_key,
    )

    cmp_result_by_type = _group_by_type(repr_cmp_result)
    type_explanations_list: typing.List[typing.List[str]] = (
        _to_explanations(cmp_result_by_type)
    )

    explanation: typing.List[str] = [
        'failed for %s:' % _get_summary(left, right, '=='),
    ]
    for type_explanations in type_explanations_list:
        if add_empty_lines:
            explanation.append('')
        explanation.extend(type_explanations)

    if add_full_diff:
        if add_empty_lines:
            explanation.append('')
        explanation.extend(_get_full_diff(left, right))
    return explanation


def _cmp_sort_key(part):
    # for right sequence order of int keys (not like ['0', '1', '10', '2'])
    key, _cmp_info, repr_info = part
    str_part = []
    int_part = []
    for sub_key in key:
        if isinstance(sub_key, int):
            int_part.append(sub_key)
        else:
            str_part.append(str(sub_key))
    return tuple(str_part), tuple(int_part), '\n'.join(repr_info)


def _make_length_info(value):
    return '<class %r; length=%d>' % (type(value).__name__, len(value))


def _make_repr_lines(cmp_info, repr_func):
    def _get_repr_lines(value):
        return repr_func(value).splitlines()

    if cmp_info.cmp_type == CMP_EXTRA_RIGHT:
        repr_lines = _merge_lines(
            ['%s value:' % cmp_info.parent_type.__name__],
            _get_repr_lines(cmp_info.right_value),
        )
    elif cmp_info.cmp_type == CMP_EXTRA_LEFT:
        repr_lines = _merge_lines(
            ['%s value:' % cmp_info.parent_type.__name__],
            _get_repr_lines(cmp_info.left_value),
        )
    elif cmp_info.cmp_type == CMP_INCONSISTENCY_TYPES:
        info = '%s != %s' % (cmp_info.left_value, cmp_info.right_value)
        repr_lines = [info]
    elif cmp_info.cmp_type == CMP_SIMPLE_DIFF:
        repr_lines = _merge_lines(
            _get_repr_lines(cmp_info.left_value),
            _get_repr_lines(cmp_info.right_value),
            connector='!=',
        )
        if len(repr_lines) > 1:
            repr_lines.insert(0, '')
    else:
        raise ValueError(
            'Incorrect cmp type %s: %s' % (cmp_info.cmp_type, cmp_info),
        )
    return repr_lines


def _merge_lines(first_lines, extra_lines, connector=None):
    group = []
    if len(first_lines) > 1 or len(extra_lines) > 1:
        group.extend(first_lines)
        if connector is not None:
            group.append(connector)
        group.extend(extra_lines)
    else:
        if connector is not None:
            line = ' '.join((*first_lines, connector, *extra_lines))
        else:
            line = ' '.join((*first_lines, *extra_lines))
        group.append(line)
    return group


def _format_cmp_part(repr_key, repr_lines):
    ident = '    '
    prefix = ' * '
    if repr_key is not NOT_A_KEY:
        lines = [('%s%s: ' % (prefix, repr_key)) + repr_lines[0]]
        extra_lines_ind = 1
    elif repr_lines[0] != '':
        lines = [prefix + repr_lines[0]]
        extra_lines_ind = 1
    else:
        lines = [prefix + (' ' * (len(ident) - len(prefix))) + repr_lines[1]]
        extra_lines_ind = 2
    for line in repr_lines[extra_lines_ind:]:
        lines.append(ident + line)
    return lines


def _get_summary(left, right, oper):
    """Original pytest summary"""
    # 15 chars indentation, 1 space around operator
    width = 80 - 15 - len(oper) - 2
    left_repr = py.io.saferepr(left, maxsize=int(width // 2))
    right_repr = py.io.saferepr(right, maxsize=width - len(left_repr))

    return '%s %s %s' % (left_repr, oper, right_repr)


def _get_full_diff(left, right):
    """Original pytest full diff"""
    # dynamic import to speedup pytest
    import difflib

    left_formatting = pprint.pformat(left).splitlines()
    right_formatting = pprint.pformat(right).splitlines()
    explanation = ['Full diff:']
    explanation.extend(
        line.strip()
        for line in difflib.ndiff(left_formatting, right_formatting)
    )
    return explanation


def _match_type(obj):
    obj_type = type(obj)
    if issubclass(obj_type, matching.AnyString):
        return str
    return obj_type
