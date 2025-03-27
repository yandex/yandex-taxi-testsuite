import collections
import contextlib
import enum
import io
import itertools
import logging
import typing

import pytest

from testsuite._internal import compare_transform


class AssertMode(enum.Enum):
    DEFAULT = 'default'
    COMBINE = 'combine'
    ANALYZE = 'analyze'


class AssertionPlugin:
    def __init__(self, assert_mode):
        self._disabled = False
        self._assert_mode = assert_mode

    @contextlib.contextmanager
    def disabled(self):
        saved = self._disabled
        try:
            self._disabled = True
            yield
        finally:
            self._disabled = saved

    def pytest_assertrepr_compare(
        self,
        config,
        op: str,
        left: typing.Any,
        right: typing.Any,
    ):
        if op != '==' or self._disabled:
            return None

        comparator = compare_transform.CompareTransform()
        try:
            mapped_right = comparator.visit(left, right)
        except Exception:
            logging.exception('testsuite assertrepr_compare failed:')
            return None

        with self.disabled():
            pytest_result = config.hook.pytest_assertrepr_compare(
                config=config,
                op=op,
                left=left,
                right=mapped_right,
            )
        if not pytest_result:
            return pytest_result

        output = io.StringIO()
        if comparator.errors:
            print(f'left {op} right')
            for path, errors in comparator.errors.items():
                print(f'{path}:', file=output)
                for error in errors:
                    print(f' - {error}', file=output)

        if self._assert_mode == AssertMode.COMBINE:
            print('pytest default:\n', file=output)
            for items in pytest_result:
                for item in items:
                    print(item, file=output)
        return output.getvalue().splitlines()


def pytest_configure(config):
    if config.option.assert_mode != AssertMode.DEFAULT:
        config.pluginmanager.register(
            AssertionPlugin(config.option.assert_mode)
        )


def pytest_addoption(parser: pytest.Parser):
    """
    :param parser: pytest's argument parser
    """
    group = parser.getgroup('common')
    group.addoption(
        '--assert-mode',
        choices=[i.name for i in list(AssertMode)],
        type=AssertMode,
        default=AssertMode.COMBINE,
        help='Assertion representation mode, combined by default',
    )
    group.addoption(
        '--assert-depth',
        type=int,
        default=None,
        help='Depth of assertions, use 0 for simple print different items',
    )
