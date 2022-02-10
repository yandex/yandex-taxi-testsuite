import io
import typing

import pytest

from testsuite.utils import colors

from . import exceptions


class MockserverReporterPlugin:
    _errors: typing.List[typing.Tuple[Exception, str]]

    def __init__(self, *, colors_enabled: bool):
        self._colors_enabled = colors_enabled
        self._errors = []

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(self, item):
        self._errors = []
        yield
        if self._errors:
            report = self._get_report()
            item.add_report_section('errors', 'mockserver', report)
            item.user_properties.append(('mockserver errors', report))
            first_error, _message = self._errors[0]
            raise exceptions.MockServerError(
                'There were errors while processing mockserver requests.',
            ) from first_error

    def report_error(
            self, error: Exception, message: typing.Optional[str] = None,
    ) -> None:
        if message is None:
            message = str(error)
        self._errors.append((error, message))

    def _get_report(self) -> str:
        if not self._errors:
            return ''
        output = io.StringIO()
        if self._colors_enabled:
            output.write(colors.Colors.BRIGHT_RED)
        for index, (_error, message) in enumerate(self._errors):
            if index > 0:
                output.write('\n\n')
            output.write(message)
        if self._colors_enabled:
            output.write(colors.Colors.DEFAULT)
        return output.getvalue()
