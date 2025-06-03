import contextlib
import enum
import io
import logging
import typing

import pytest

from testsuite._internal import compare_transform


class AssertMode(enum.Enum):
    DEFAULT = 'default'
    COMBINE = 'combine'
    ANALYZE = 'analyze'


class AssertionPlugin:
    def __init__(self, assert_mode, transform_mode):
        self._disabled = False
        self._assert_mode = assert_mode
        self._transform_mode = transform_mode

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
        config: pytest.Config,
        op: str,
        left: typing.Any,
        right: typing.Any,
    ):
        if op != '==' or self._disabled:
            return None

        comparator = compare_transform.CompareTransform(self._transform_mode)
        try:
            mapped_left, mapped_right = comparator.visit(left, right)
        except Exception:
            logging.exception('testsuite assertrepr_compare failed:')
            return None

        with self.disabled():
            pytest_result = config.hook.pytest_assertrepr_compare(
                config=config,
                op=op,
                left=mapped_left,
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


def pytest_configure(config: pytest.Config):
    assert_mode = AssertMode(config.option.assert_mode)
    transform_mode = compare_transform.TransformMode(
        config.option.assert_transform_mode
    )

    if assert_mode != AssertMode.DEFAULT.name:
        config.pluginmanager.register(
            AssertionPlugin(assert_mode, transform_mode)
        )


def pytest_addoption(parser: pytest.Parser):
    """
    :param parser: pytest's argument parser
    """
    group = parser.getgroup('common')
    group.addoption(
        '--assert-mode',
        choices=[i.value for i in list(AssertMode)],
        type=str,
        default=AssertMode.COMBINE.value,
        help='Assertion representation mode, combined by default',
    )
    group.addoption(
        '--assert-depth',
        type=int,
        default=None,
        help='Depth of assertions, use 0 for simple print different items',
    )
    group.addoption(
        '--assert-transform-mode',
        choices=[i.value for i in list(compare_transform.TransformMode)],
        type=str,
        default=compare_transform.TransformMode.DEFAULT.value,
        help='Transformation mode in assertion representation',
    )
