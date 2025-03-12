import collections
import contextlib
import typing

import py.io

from testsuite import matching

ListOrTuple = (list, tuple)
SetTypes = (set, frozenset)


class CompareTransform:
    path: typing.List[str]
    errors: typing.DefaultDict[str, typing.List[str]]

    def __init__(self):
        self.path = ['left']
        self.errors = collections.defaultdict(list)

    def report_error(self, msg: str) -> None:
        path = ''.join(self.path)
        self.errors[path].append(msg)

    def visit(self, left: typing.Any, right: typing.Any) -> typing.Any:
        if left == right:
            return left
        if isinstance(left, ListOrTuple):
            return self.visit_list(left, right)
        elif isinstance(left, dict):
            return self.visit_dict(left, right)
        elif isinstance(left, SetTypes):
            return self.visit_set(left, right)

        self.report_error(f'{left!r} != {right!r}')
        return right

    def visit_list(
        self,
        left: typing.Union[list, tuple],
        right: typing.Any,
    ) -> typing.List:
        left, right = _resolve_value(left, right)
        if not isinstance(right, list):
            self.report_error(
                f'type mismatch expected: {type(left)}, got: {type(right)}',
            )
            return right
        left_len = len(left)
        right_len = len(right)
        if left_len != right_len:
            self.report_error(
                f'list length does not match: len(left)={left_len} len(right)={right_len}',
            )

        result = []
        left_items, right_items = _resolve_value(left, right)
        for idx, (item_left, item_right) in enumerate(
            zip(left_items, right_items),
        ):
            with self.push(f'[{idx}]'):
                result.append(self.visit(item_left, item_right))
        return result

    def visit_dict(self, left: typing.Dict, right: typing.Any) -> typing.Dict:
        left, right = _resolve_value(left, right)
        if not isinstance(right, dict):
            self.report_error(
                f'dict expected on the right, got {type(right)} instead'
            )
            return right
        left_len = len(left)
        right_len = len(right)
        if left_len != right_len:
            self.report_error(
                f'dict length does not match len(left)={left_len}, len(right)={right_len}'
            )

        common_keys = left.keys() & right.keys()
        left_only = left.keys() - common_keys
        right_only = right.keys() - common_keys

        result = {}
        if left_only:
            self.report_error(
                f'extra keys on the left: {_format_keys(left_only)}'
            )
        if right_only:
            self.report_error(
                f'extra keys on the right: {_format_keys(right_only)}'
            )
        for key in right_only:
            result[key] = right[key]
        for key in common_keys:
            with self.push(f'["{key}"]'):
                result[key] = self.visit(left[key], right[key])
        return result

    def visit_set(
        self,
        left: typing.Union[set, frozenset],
        right: typing.Any,
    ) -> typing.Set:
        if not isinstance(right, SetTypes):
            self.report_error(f'type mismatch, set expected: {left} != {right}')
            return right
        left_len = len(left)
        right_len = len(right)
        if len(left) != len(right):
            self.report_error(
                f'set length does not match: len(left)={left_len}, len(right)={right_len}',
            )
        common_keys = left & right
        left_only = left - common_keys
        right_only = right - common_keys
        result = common_keys.copy()
        if left_only:
            self.report_error(f'extra keys on the left: {left_only}')
        if right_only:
            self.report_error(f'extra item on the right: {right_only}')
        for key in right_only:
            result.add(key)
        return set(result)

    @contextlib.contextmanager
    def push(self, path: str):
        try:
            self.path.append(path)
            yield
        finally:
            self.path.pop(-1)


def _resolve_length(obj):
    if hasattr(obj, '__testsuite_len__'):
        return obj.__testsuite_len__()
    return len(obj)


def _resolve_value(left, right):
    if hasattr(left, '__testsuite_resolve_value__'):
        return left.__testsuite_resolve_value__(right), right
    if hasattr(right, '__testsuite_resolve_value__'):
        return left, right.__testsuite_resolve_value__(left)
    return left, right


def _match_types(left_types, right_types):
    if not isinstance(left_types, tuple):
        left_types = (left_types,)
    if not isinstance(right_types, tuple):
        right_types = (right_types,)
    for left_type in left_types:
        for right_type in right_types:
            if issubclass(right_type, left_type):
                return True
    return False


def _format_keys(keys):
    return ', '.join(repr(key) for key in sorted(keys))
