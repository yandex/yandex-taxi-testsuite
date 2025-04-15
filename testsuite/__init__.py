import pytest

from . import types as annotations  # noqa: F401
from ._version import __version__  # noqa: F401

pytest.register_assert_rewrite(
    'testsuite.plugins',
    'testsuite.databases',
    'testsuite.utils.ordered_object',
)
