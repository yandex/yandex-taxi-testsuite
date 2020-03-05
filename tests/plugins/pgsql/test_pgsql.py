import os.path

import pytest

from testsuite.databases.pgsql import discover

SQLDATA_PATH = os.path.join(
    os.path.dirname(__file__), 'static/postgresql/schemas',
)

MIGRATIONS = os.path.join(
    os.path.dirname(__file__), 'static/postgresql/migrations',
)


@pytest.fixture(scope='session')
def pgsql_local(pgsql_local_create):
    databases = discover.find_databases('service', SQLDATA_PATH, MIGRATIONS)

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
