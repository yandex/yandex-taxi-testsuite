import pathlib

import pytest

from testsuite.databases.pgsql import discover

BASE_PATH = pathlib.Path(__file__).parent / 'static/postgresql'
SQLDATA_PATH = BASE_PATH / 'schemas'
MIGRATIONS = BASE_PATH / 'migrations'


@pytest.fixture(scope='session')
def pgsql_local(pgsql_local_create):
    databases = discover.find_schemas('service', [SQLDATA_PATH, MIGRATIONS])

    assert sorted(databases) == [
        'foo',
        'multidir',
        'pgmigrate',
        'pgmigrate_sharded',
    ]
    assert databases['foo'].dbname == 'foo'
    assert len(databases['foo'].shards) == 2
    assert databases['foo'].shards[0].dbname == 'service_foo_0'
    assert databases['foo'].shards[1].dbname == 'service_foo_1'

    return pgsql_local_create(list(databases.values()))


def test_shards(pgsql):
    for shard_id, dbname in enumerate(['foo@0', 'foo@1']):
        cursor = pgsql[dbname].cursor()
        cursor.execute('SELECT value from foo')
        result = list(row[0] for row in cursor)
        cursor.close()
        assert result == ['This is shard %d' % shard_id]


def test_pgsql_apply_queries(pgsql):
    pgsql['foo@0'].apply_queries(['INSERT INTO foo VALUES (\'mark0\')'])
    pgsql['foo@1'].apply_queries(['INSERT INTO foo VALUES (\'mark1\')'])

    for shard_id, dbname in enumerate(['foo@0', 'foo@1']):
        cursor = pgsql[dbname].cursor()
        cursor.execute('SELECT value from foo')
        result = list(row[0] for row in cursor)
        cursor.close()
        assert result == ['mark%d' % shard_id]


@pytest.mark.pgsql('foo@0', queries=['INSERT INTO foo VALUES (\'mark0\')'])
@pytest.mark.pgsql('foo@1', queries=['INSERT INTO foo VALUES (\'mark1\')'])
def test_pgsql_mark_queries(pgsql):
    for shard_id, dbname in enumerate(['foo@0', 'foo@1']):
        cursor = pgsql[dbname].cursor()
        cursor.execute('SELECT value from foo')
        result = list(row[0] for row in cursor)
        cursor.close()
        assert result == ['mark%d' % shard_id]


@pytest.mark.pgsql('foo@0', files=['custom_foo@0.sql'])
@pytest.mark.pgsql('foo@1', directories=['custom_foo@1'])
def test_pgsql_mark_files(pgsql):
    for shard_id, dbname in enumerate(['foo@0', 'foo@1']):
        cursor = pgsql[dbname].cursor()
        cursor.execute('SELECT value from foo')
        result = list(row[0] for row in cursor)
        cursor.close()
        assert result == ['custom%d' % shard_id]


def test_multidir_schema(pgsql):
    cursor = pgsql['multidir'].cursor()
    cursor.execute('SELECT value from multidir1')
    result = sorted(row[0] for row in cursor)
    assert result == ['first', 'second']

    cursor = pgsql['multidir'].cursor()
    cursor.execute('SELECT value from multidir2')
    result = sorted(row[0] for row in cursor)
    assert result == []


def test_migrations(pgsql):
    cursor = pgsql['pgmigrate'].cursor()
    cursor.execute('SELECT value from migrations')
    result = list(row[0] for row in cursor)
    assert result == []


def test_migrations_shards(pgsql):
    cursor = pgsql['pgmigrate_sharded@0'].cursor()
    cursor.execute('SELECT value0 from migrations')
    result = list(row[0] for row in cursor)
    assert result == []

    cursor = pgsql['pgmigrate_sharded@1'].cursor()
    cursor.execute('SELECT value1 from migrations')
    result = list(row[0] for row in cursor)
    assert result == []


def test_reconnect(pgsql):
    pgsql['foo@0'].conn.close()
    with pytest.warns(UserWarning):
        assert pgsql['foo@0'].conn is not None


@pytest.mark.pgsql('foo@0', queries=['INSERT INTO foo VALUES (\'mark1\')'])
def test_dict_cursor(pgsql):
    cursor = pgsql['foo@0'].dict_cursor()
    cursor.execute('SELECT value from foo')
    row = cursor.fetchone()
    assert row == ['mark1']
    assert {**row} == {'value': 'mark1'}
