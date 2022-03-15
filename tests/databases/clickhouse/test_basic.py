import pathlib

import pytest

from testsuite.databases.clickhouse import discover

SCHEMAS_DIR = pathlib.Path(__file__).parent.joinpath('schemas')


@pytest.fixture(scope='session')
def clickhouse_local():
    return discover.find_schemas([SCHEMAS_DIR])


@pytest.mark.clickhouse(
    'testdb', queries=['INSERT INTO foo(id, value) VALUES(1, \'one\')'],
)
def test_apply(clickhouse):
    clickhouse['testdb'].execute(
        'INSERT INTO foo(id, value) VALUES(3, \'three\')',
    )
    res = clickhouse['testdb'].execute('SELECT * FROM foo ORDER BY id')

    assert res == [(1, 'one'), (3, 'three')]


def test_static_apply(clickhouse):
    res = clickhouse['testdb'].execute('SELECT * FROM foo')

    assert res == [(2, 'two')]
