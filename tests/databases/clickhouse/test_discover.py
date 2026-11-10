from testsuite.databases.clickhouse import discover, service


def test_find_schemas_dbprefix(tmp_path):
    (tmp_path / 'testdb.sql').write_text('CREATE TABLE foo (id INT);')
    schemas = discover.find_schemas([tmp_path])
    assert schemas['testdb'].dbname == 'testsuite-testdb'
    schemas = discover.find_schemas([tmp_path], dbprefix='testsuite-gw1-')
    assert schemas['testdb'].dbname == 'testsuite-gw1-testdb'


def test_get_dbprefix(monkeypatch):
    monkeypatch.delenv('TESTSUITE_CLICKHOUSE_DBNAME_PREFIX', raising=False)
    assert service.get_dbprefix() == 'testsuite-'
    monkeypatch.setenv('TESTSUITE_CLICKHOUSE_DBNAME_PREFIX', 'gw1')
    assert service.get_dbprefix() == 'testsuite-gw1-'
