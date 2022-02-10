import pytest

from testsuite.databases.pgsql import connection


@pytest.mark.parametrize(
    'uri, expected',
    [
        ('postgresql:///', connection.PgConnectionInfo()),
        ('postgres:///', connection.PgConnectionInfo()),
        ('postgres://', connection.PgConnectionInfo()),
        (
            'postgres://localhost',
            connection.PgConnectionInfo(host='localhost'),
        ),
        ('postgres://0.0.0.0', connection.PgConnectionInfo(host='0.0.0.0')),
        ('postgres://[::1]', connection.PgConnectionInfo(host='::1')),  # ipv6
        (
            'postgres://%2Fvar%2Flib%2Fpostgresql/',
            connection.PgConnectionInfo(host='/var/lib/postgresql'),
        ),
        (
            'postgres:///?host=/var/lib/postgresql',
            connection.PgConnectionInfo(host='/var/lib/postgresql'),
        ),
        ('postgres:///dbname', connection.PgConnectionInfo(dbname='dbname')),
        (
            'postgres://usr:123@host:5433/',
            connection.PgConnectionInfo(
                host='host', port=5433, user='usr', password='123',
            ),
        ),
        (
            'postgres:///?host=host&port=5433&password=123&user=usr',
            connection.PgConnectionInfo(
                host='host', port=5433, user='usr', password='123',
            ),
        ),
        (
            'postgres:///?options=-c%20geqo%3Doff&sslmode=require',
            connection.PgConnectionInfo(
                options='-c geqo=off', sslmode='require',
            ),
        ),
    ],
)
def test_parse_uri(uri: str, expected: connection.PgConnectionInfo):
    parsed = connection.parse_connection_string(uri)
    assert parsed == expected


@pytest.mark.parametrize(
    'dsn,expected',
    [
        # quoted empty value
        ('host=\'\'', connection.PgConnectionInfo(host='')),
        # quoted whitespace
        ('host=\'a b\'', connection.PgConnectionInfo(host='a b')),
        # escaped quote
        (r'host=\'', connection.PgConnectionInfo(host='\'')),
        # escaped backslash
        ('host=\\\\', connection.PgConnectionInfo(host='\\')),
        ('host=::1 port=54', connection.PgConnectionInfo(host='::1', port=54)),
        ('dbname=some_name', connection.PgConnectionInfo(dbname='some_name')),
        ('user=usr', connection.PgConnectionInfo(user='usr')),
        (
            'user=usr password=pwd',
            connection.PgConnectionInfo(user='usr', password='pwd'),
        ),
        (
            'options=\'-c geqo=off\'',
            connection.PgConnectionInfo(options='-c geqo=off'),
        ),
        ('sslmode=require', connection.PgConnectionInfo(sslmode='require')),
    ],
)
def test_parse_dsn(dsn: str, expected: connection.PgConnectionInfo):
    parsed = connection.parse_connection_string(dsn)
    assert parsed == expected
