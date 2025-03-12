import pytest

from testsuite.databases.pgsql import utils


@pytest.mark.parametrize(
    'connstr,dbname,expected',
    [
        ('host=localhost dbname=', 'foo', 'host=localhost dbname=foo'),
        (
            'postgresql://localhost/bar?p1=1&p2=2',
            'foo',
            'postgresql://localhost/foo?p1=1&p2=2',
        ),
    ],
)
@pytest.mark.nofilldb
def test_pg_replace_dbname(connstr, dbname, expected):
    assert utils.connstr_replace_dbname(connstr, dbname) == expected
