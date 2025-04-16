import sys

import pytest


class ColorsPlugin:
    def __init__(self, config):
        self._colors_enabled = _is_colors_enabled(config)

    @pytest.fixture(scope='session')
    def testsuite_colors_enabled(self) -> bool:
        return self._colors_enabled


def pytest_configure(config):
    config.pluginmanager.register(
        ColorsPlugin(config=config),
        '_colors_plugin',
    )


def _is_colors_enabled(pytestconfig) -> bool:
    option = getattr(pytestconfig.option, 'color', 'no')
    if option == 'yes':
        return True
    if option == 'auto':
        return sys.stderr.isatty()
    return False
