import pytest


@pytest.fixture(scope='session')
def pgsql_cleanup_exclude_tables():
    return frozenset({'public.no_clean_table'})
