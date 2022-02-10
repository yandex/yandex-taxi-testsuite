import pytest

from testsuite.databases.mongo import connection


@pytest.mark.parametrize(
    'uri, connection_info',
    [
        (
            'mongodb://localhost:27017/',
            connection.ConnectionInfo(
                host='localhost', port=27017, dbname=None, retry_writes=None,
            ),
        ),
        (
            'mongodb://some.host:1234/?retryWrites=false',
            connection.ConnectionInfo(
                host='some.host', port=1234, dbname=None, retry_writes=False,
            ),
        ),
        (
            'mongodb://127.0.0.1:27217/some_database?retryWrites=true',
            connection.ConnectionInfo(
                host='127.0.0.1',
                port=27217,
                dbname='some_database',
                retry_writes=True,
            ),
        ),
    ],
)
def test_parse_roundtrip(uri: str, connection_info: connection.ConnectionInfo):
    assert connection_info == connection.parse_connection_uri(uri)
    assert connection_info.get_uri() == uri


@pytest.mark.parametrize(
    'uri',
    [
        'http://localhost:27017/',  # invalid schema
        'mongodb://localhost:27017/?retryWrites=yes',  # invalid retryWrites
    ],
)
def test_when_invalid_uri_then_parse_raises_value_error(uri: str):
    with pytest.raises(ValueError):
        connection.parse_connection_uri(uri)
