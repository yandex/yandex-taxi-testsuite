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

    def visit(
        self, left: typing.Any, right: typing.Any
    ) -> typing.Tuple[typing.Any, typing.Any]:
        if left == right:
            return left, left

        left, right = _resolve_value(left, right, self.report_error)
        if isinstance(left, ListOrTuple):
            return self.visit_list(left, right)
        elif isinstance(left, dict):
            return self.visit_dict(left, right)
        elif isinstance(left, SetTypes):
            return self.visit_set(left, right)

        self.report_error(f'{left!r} != {right!r}')
        return left, right

    def visit_list(
        self,
        left: typing.Union[list, tuple],
        right: typing.Any,
    ) -> typing.Tuple:
        if not isinstance(right, list):
            self.report_error(
                f'type mismatch, list expected got: {right}',
            )
            return left, right
        left_len = len(left)
        right_len = len(right)
        if left_len != right_len:
            self.report_error(
                f'list length does not match: len(left)={left_len} len(right)={right_len}',
            )

        result = []
        for idx, (item_left, item_right) in enumerate(
            zip(left, right),
        ):
            with self.push(f'[{idx}]'):
                # TODO: map left as well
                __, right_mapped = self.visit(item_left, item_right)
                result.append(right_mapped)
        if left_len > right_len:
            for idx, item in enumerate(left[right_len:], right_len):
                self.report_error(f'[{idx}]: extra item on the left: {item!r}')
        elif right_len > left_len:
            for idx, item in enumerate(right[left_len:], left_len):
                self.report_error(f'[{idx}]: extra item on the right: {item!r}')
        return left, result

    def visit_dict(self, left: typing.Dict, right: typing.Any) -> typing.Tuple:
        if not isinstance(right, dict):
            self.report_error(
                f'dict expected on the right, got {type(right)} instead'
            )
            return left, right
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
                # TODO: map left as well
                _, right_mapped = self.visit(left[key], right[key])
                result[key] = right_mapped
        return left, result

    def visit_set(
        self,
        left: typing.Union[set, frozenset],
        right: typing.Any,
    ) -> typing.Tuple:
        if not isinstance(right, SetTypes):
            self.report_error(
                f'type mismatch, set expected got: {right}',
            )
            return left, right
        common_keys = left & right
        left_only = left - common_keys
        right_only = right - common_keys
        result = common_keys.copy()
        if left_only:
            self.report_error(
                f'extra items on the left: {_format_keys(left_only)}',
            )
        if right_only:
            self.report_error(
                f'extra items on the right: {_format_keys(right_only)}',
            )
        for key in right_only:
            result.add(key)
        return left, set(result)

    @contextlib.contextmanager
    def push(self, path: str):
        try:
            self.path.append(path)
            yield
        finally:
            self.path.pop(-1)


def _resolve_value(left, right, reporter):
    if hasattr(left, '__testsuite_resolve_value__'):
        return left.__testsuite_resolve_value__(right, reporter), right
    if hasattr(right, '__testsuite_resolve_value__'):
        return left, right.__testsuite_resolve_value__(left, reporter)
    return left, right


def _format_keys(keys):
    return ', '.join(repr(key) for key in sorted(keys))
