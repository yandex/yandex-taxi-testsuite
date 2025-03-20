import pytest

from ._version import __version__

pytest.register_assert_rewrite(
    'testsuite.plugins',
    'testsuite.databases',
    'testsuite.utils.ordered_object',
)
