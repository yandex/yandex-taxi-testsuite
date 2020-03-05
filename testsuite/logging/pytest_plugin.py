import logging
import sys
import typing

import pytest

from . import logger


class Plugin:
    def __init__(
            self,
            line_logger: logger.LineLogger,
            testsuite_logger: logger.Logger,
            colors_enabled: bool,
            ensure_newline: bool,
    ):
        self._line_logger = line_logger
        self._testsuite_logger = testsuite_logger
        self._colors_enabled = colors_enabled
        self._ensure_newline = ensure_newline
        root_logger = logging.getLogger()
        handler = logger.Handler(writer=testsuite_logger)
        handler.setFormatter(
            logger.ColoredLevelFormatter(colors_enabled=self._colors_enabled),
        )
        root_logger.addHandler(handler)

    @property
    def testsuite_logger(self):
        return self._testsuite_logger

    def pytest_runtest_setup(self):
        # At this point output is already captured
        self._line_logger.resume(sys.stderr, self._ensure_newline)

    def pytest_runtest_logfinish(self):
        self._line_logger.suspend()

    def pytest_sessionfinish(self):
        # Flush logger buffer to stderr
        self._line_logger.resume(sys.stderr, True)


class Hookspec:
    # pylint: disable=invalid-name
    def pytest_override_testsuite_logger(
            self, config, line_logger: logger.LineLogger, colors_enabled: bool,
    ) -> typing.Optional[logger.Logger]:
        """Return logger to be used instead of standard one"""


def pytest_addhooks(pluginmanager):
    pluginmanager.add_hookspecs(Hookspec)


def pytest_configure(config):
    colors_enabled = _should_enable_color(config)
    line_logger = logger.LineLogger()
    overrides = config.pluginmanager.hook.pytest_override_testsuite_logger(
        config=config, line_logger=line_logger, colors_enabled=colors_enabled,
    )
    if overrides:
        testsuite_logger = overrides[-1]
    else:
        testsuite_logger = logger.Logger(line_logger)
    plugin = Plugin(
        line_logger,
        testsuite_logger,
        colors_enabled=colors_enabled,
        ensure_newline=config.option.capture == 'no',
    )
    config.pluginmanager.register(plugin, 'testsuite_logger')


@pytest.fixture(scope='session')
def testsuite_logger(pytestconfig):
    plugin: Plugin = pytestconfig.pluginmanager.getplugin('testsuite_logger')
    return plugin.testsuite_logger


def _should_enable_color(pytestconfig) -> bool:
    option = getattr(pytestconfig.option, 'color', 'no')
    return option == 'yes' or option == 'auto' and sys.stderr.isatty()
