import contextlib
import typing

import psycopg2
import psycopg2.extensions

from testsuite import utils

from . import connection

CREATE_DATABASE_TEMPLATE = """
CREATE DATABASE "{}" WITH TEMPLATE = template0
ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C'
"""

DATABASE_EXISTS_TEMPLATE = 'SELECT 1 FROM pg_database WHERE datname=%s'

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS applied_schemas (
    db_name TEXT PRIMARY KEY,
    schema_hash TEXT
);
"""

UPDATE_DB_HASH_TEMPLATE = """
INSERT INTO applied_schemas (db_name, schema_hash)
VALUES (%(dbname)s, %(hash)s)
ON CONFLICT (db_name) DO UPDATE SET
    schema_hash = %(hash)s
WHERE applied_schemas.db_name = %(dbname)s
"""
SELECT_DB_HASH_TEMPLATE = 'SELECT db_name, schema_hash FROM applied_schemas'
TESTSUITE_DB_NAME = 'testsuite'


class AppliedSchemaHashes:
    def __init__(
            self,
            postgres_db_connection: psycopg2.extensions.connection,
            base_conninfo: connection.PgConnectionInfo,
    ):
        self._postgres_db_connection = postgres_db_connection
        self._conninfo = base_conninfo.replace(dbname=TESTSUITE_DB_NAME)

    def get_hash(self, dbname: str) -> typing.Optional[str]:
        """Get hash of schema applied to a database"""
        return self._hash_by_dbname.get(dbname, None)

    def set_hash(self, dbname: str, schema_hash: str):
        """Store in testsuite database and remember locally a hash of schema
        applied to a database
        """
        self._hash_by_dbname[dbname] = schema_hash
        cursor = self._connection.cursor()
        with contextlib.closing(cursor):
            cursor.execute(
                UPDATE_DB_HASH_TEMPLATE,
                {'dbname': dbname, 'hash': schema_hash},
            )

    @utils.cached_property
    def _hash_by_dbname(self) -> typing.Dict[str, str]:
        cursor = self._connection.cursor()
        with contextlib.closing(cursor):
            cursor.execute(SELECT_DB_HASH_TEMPLATE)
            return {entry[0]: entry[1] for entry in cursor}

    @utils.cached_property
    def _connection(self) -> psycopg2.extensions.connection:
        self._create_db()
        conn = psycopg2.connect(self._conninfo.get_uri())
        conn.autocommit = True
        cursor = conn.cursor()
        with contextlib.closing(cursor):
            cursor.execute(CREATE_TABLE_SQL)
        return conn

    def _create_db(self) -> None:
        cursor = self._postgres_db_connection.cursor()
        with contextlib.closing(cursor):
            cursor.execute(DATABASE_EXISTS_TEMPLATE, (TESTSUITE_DB_NAME,))
            db_exists = any(cursor)
            if db_exists:
                return
            cursor.execute(CREATE_DATABASE_TEMPLATE.format(TESTSUITE_DB_NAME))
