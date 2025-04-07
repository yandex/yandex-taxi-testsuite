import pytest

pytest_plugins = [
    'testsuite.pytest_plugin',
    'testsuite.databases.pgsql.pytest_plugin',
]


@pytest.fixture(scope='session')
def pgsql_cleanup_exclude_tables():
    return frozenset({'public.no_clean_table'})
