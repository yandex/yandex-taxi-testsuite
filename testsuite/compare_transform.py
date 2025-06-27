from __future__ import annotations

import collections
import contextlib
import enum
import typing

import py.io

SetTypes = (set, frozenset)


class TypeTransformer:
    def __init__(
        self,
        comparator: typing.Callable[
            [typing.Any, typing.Any, CompareTransform],
            tuple[typing.Any, typing.Any],
        ],
        types: type | tuple | None = None,
        matcher: typing.Callable[[typing.Any], bool] | None = None,
    ):
        assert types or matcher, (
            'either types or matcher must be specified for transformer'
        )

        self._comparator = comparator
        self._matcher = matcher or (lambda x: isinstance(x, types))  # type: ignore[arg-type]

    def matches(self, value: typing.Any) -> bool:
        return self._matcher(value)

    def compare_and_transform(
        self, left: typing.Any, right: typing.Any, comparator: CompareTransform
    ) -> tuple[typing.Any, typing.Any]:
        return self._comparator(left, right, comparator)


class TransformMode(enum.Enum):
    DEFAULT = 'default'
    EXPERIMENTAL = 'experimental'


class CompareTransform:
    def __init__(
        self, mode: TransformMode, transformers: list[TypeTransformer]
    ):
        self.path: list[str] = ['left']
        self.errors: typing.DefaultDict[str, list[str]] = (
            collections.defaultdict(list)
        )
        self._mode = mode
        self._transformers = transformers

    def _try_match_transformer(
        self, value: typing.Any
    ) -> TypeTransformer | None:
        return next(
            (
                transformer
                for transformer in self._transformers
                if transformer.matches(value)
            ),
            None,
        )

    def _resolve_values(
        self, left: typing.Any, right: typing.Any
    ) -> tuple[typing.Any, typing.Any]:
        if self._mode == TransformMode.DEFAULT:
            return _resolve_values_default(left, right, self.report_error)
        return _resolve_values_experimental(left, right, self.report_error)

    def report_error(
        self, message: str, path: str | tuple | list | None = None
    ) -> None:
        self.errors[_build_path(self.path, path)].append(message)

    @contextlib.contextmanager
    def push_path(self, path: str) -> typing.Generator:
        try:
            self.path.append(path)
            yield
        finally:
            self.path.pop(-1)

    def compare_and_transform(
        self, left: typing.Any, right: typing.Any
    ) -> tuple[typing.Any, typing.Any]:
        if left == right:
            return left, right

        left, right = self._resolve_values(left, right)

        transformer = self._try_match_transformer(left)
        if transformer is not None:
            return transformer.compare_and_transform(left, right, self)

        self.report_error(f'{py.io.saferepr(left)} != {py.io.saferepr(right)}')
        return left, right


def default_transformers() -> list[TypeTransformer]:
    return [
        TypeTransformer(types=list, comparator=_compare_and_transform_list),
        TypeTransformer(types=dict, comparator=_compare_and_transform_dict),
        TypeTransformer(types=SetTypes, comparator=_compare_and_transform_set),
    ]


def _resolve_values_default(left, right, reporter):
    if hasattr(left, '__testsuite_resolve_value__'):
        return left.__testsuite_resolve_value__(right, reporter), right
    if hasattr(right, '__testsuite_resolve_value__'):
        return left, right.__testsuite_resolve_value__(left, reporter)
    return left, right


def _resolve_values_experimental(left, right, reporter):
    if hasattr(left, '__testsuite_adjust_values__'):
        return left.__testsuite_adjust_values__(right, reporter)
    if hasattr(right, '__testsuite_adjust_values__'):
        return right.__testsuite_adjust_values__(left, reporter)[::-1]
    return left, right


def _build_path(path, extra_path: str | list | tuple | None = None):
    realpath = path.copy()
    if isinstance(extra_path, str):
        realpath.append(extra_path)
    elif isinstance(extra_path, (tuple, list)):
        realpath.extend(extra_path)
    return ''.join(realpath)


def _format_keys(keys):
    return ', '.join(repr(key) for key in sorted(keys))


def _compare_and_transform_list(
    left, right, comparator: CompareTransform
) -> tuple:
    if not isinstance(right, list):
        comparator.report_error(
            f'list expected on the right got {py.io.saferepr(right)} instead',
        )
        return left, right
    left_len = len(left)
    right_len = len(right)
    if left_len != right_len:
        comparator.report_error(
            f'list length does not match: len(left)={left_len} len(right)={right_len}',
        )

    left_result = []
    right_result = []
    for idx, (item_left, item_right) in enumerate(
        zip(left, right),
    ):
        with comparator.push_path(f'[{idx}]'):
            left_mapped, right_mapped = comparator.compare_and_transform(
                item_left, item_right
            )
            left_result.append(left_mapped)
            right_result.append(right_mapped)
    if left_len > right_len:
        for idx, item in enumerate(left[right_len:], right_len):
            comparator.report_error(
                f'[{idx}]: extra item on the left: {py.io.saferepr(item)}'
            )
            left_result.append(item)
    elif right_len > left_len:
        for idx, item in enumerate(right[left_len:], left_len):
            comparator.report_error(
                f'[{idx}]: extra item on the right: {py.io.saferepr(item)}'
            )
            right_result.append(item)
    return left_result, right_result


def _compare_and_transform_dict(
    left, right, comparator: CompareTransform
) -> tuple:
    if not isinstance(right, dict):
        comparator.report_error(
            f'dict expected on the right, got {py.io.saferepr(right)} instead'
        )
        return left, right
    left_len = len(left)
    right_len = len(right)
    if left_len != right_len:
        comparator.report_error(
            f'dict length does not match len(left)={left_len}, len(right)={right_len}'
        )

    common_keys = left.keys() & right.keys()
    left_only = left.keys() - common_keys
    right_only = right.keys() - common_keys

    left_result = {}
    right_result = {}

    for key in common_keys | left_only:
        left_result[key] = left[key]

    if left_only:
        comparator.report_error(
            f'extra keys on the left: {_format_keys(left_only)}'
        )
    if right_only:
        comparator.report_error(
            f'extra keys on the right: {_format_keys(right_only)}'
        )
    for key in right_only:
        right_result[key] = right[key]
    for key in common_keys:
        with comparator.push_path(f'[{key!r}]'):
            left_mapped, right_mapped = comparator.compare_and_transform(
                left[key], right[key]
            )
            left_result[key] = left_mapped
            right_result[key] = right_mapped
    return left_result, right_result


def _compare_and_transform_set(
    left, right, comparator: CompareTransform
) -> tuple:
    if not isinstance(right, SetTypes):
        comparator.report_error(
            f'set expected on the right got {py.io.saferepr(right)} instead',
        )
        return left, right
    common_keys = left & right
    left_only = left - common_keys
    right_only = right - common_keys
    right_result = set(common_keys)
    if left_only:
        comparator.report_error(
            f'extra items on the left: {_format_keys(left_only)}',
        )
    if right_only:
        comparator.report_error(
            f'extra items on the right: {_format_keys(right_only)}',
        )
    for key in right_only:
        right_result.add(key)
    if isinstance(left, frozenset):
        return left, frozenset(right_result)
    return left, set(right_result)
