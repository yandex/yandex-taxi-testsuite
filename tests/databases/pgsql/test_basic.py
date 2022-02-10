import pathlib

import pytest

from testsuite.databases.pgsql import discover

SCHEMAS_DIR = pathlib.Path(__file__).parent.joinpath('schemas')


@pytest.fixture(scope='session')
def pgsql_local(pgsql_local_create):
    databases = discover.find_schemas('service', [SCHEMAS_DIR])
    return pgsql_local_create(list(databases.values()))


@pytest.mark.pgsql('testdb', files=['test_file_data.sql'])
def test_file_data(pgsql):
    cursor = pgsql['testdb'].cursor()

    cursor.execute('select * from foo order by id')
    assert cursor.fetchall() == [(1, 'one'), (2, 'two')]

    cursor.execute('select * from no_clean_table order by id')
    assert cursor.fetchall() == [(1, 'one'), (2, 'two')]
