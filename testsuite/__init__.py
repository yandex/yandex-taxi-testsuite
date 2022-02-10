import pytest

pytest.register_assert_rewrite(
    'testsuite.plugins',
    'testsuite.databases',
    'testsuite.utils.ordered_object',
)
