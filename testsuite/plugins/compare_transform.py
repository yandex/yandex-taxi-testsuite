from __future__ import annotations

import pytest

from testsuite import compare_transform


class Hookspec:
    def pytest_register_compare_transform_hooks(self):
        pass


class CompareTransformPlugin:
    def __init__(self, mode: compare_transform.TransformMode):
        self._compare_transform_hooks: list[tuple] = []
        self._mode: compare_transform.TransformMode = mode

    def comparator(self):
        return compare_transform.CompareTransform(
            self._mode, self._compare_transform_hooks
        )

    def pytest_sessionstart(self, session):
        self._compare_transform_hooks = list(
            session.config.pluginmanager.hook.pytest_register_compare_transform_hooks()
        )

    def pytest_addhooks(self, pluginmanager):
        pluginmanager.add_hookspecs(Hookspec)


def pytest_configure(config):
    config.pluginmanager.register(
        CompareTransformPlugin(config.option.compare_transform_mode),
        'compare_transform',
    )


def pytest_addoption(parser: pytest.Parser):
    """
    :param parser: pytest's argument parser
    """
    group = parser.getgroup('common')

    group.addoption(
        '--compare-transform-mode',
        choices=list(compare_transform.TransformMode),
        type=compare_transform.TransformMode,
        default=compare_transform.TransformMode.DEFAULT,
        help='Transformation mode in assertion representation',
    )
