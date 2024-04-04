import pathlib

import pytest

from testsuite.databases.pgsql import discover

MIGRATIONS = pathlib.Path(__file__).parent / 'static/pgmigrate_errors'


@pytest.fixture(scope='session')
def pgsql_local(pgsql_local_create):
    databases = discover.find_schemas('service', [MIGRATIONS])

    assert sorted(databases) == [
        'pgmigrate',
    ]

    return pgsql_local_create(list(databases.values()))


def test_pgmigrate_error(pgsql):
    pass
