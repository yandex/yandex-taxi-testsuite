import contextlib
import logging
import os
import time
import typing

import psycopg2
import psycopg2.extensions

from testsuite import utils as testsuite_utils
from testsuite.environment import shell

from . import exceptions
from . import utils

logger = logging.getLogger(__name__)

CREATE_DATABASE_TEMPLATE = """
CREATE DATABASE "{}" WITH TEMPLATE = template0
ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C'
"""
DROP_DATABASE_TEMPLATE = 'DROP DATABASE IF EXISTS "{}"'
LIST_TABLES_SQL = """
SELECT CONCAT(table_schema, '.', table_name)
FROM information_schema.tables
WHERE table_schema != 'information_schema' AND
table_schema != 'pg_catalog' AND table_type = 'BASE TABLE'
ORDER BY table_schema,table_name
"""

TRUNCATE_SQL_TEMPLATE = 'TRUNCATE TABLE {tables} RESTART IDENTITY'
TRUNCATE_RETRIES = 5
TRUNCATE_RETRY_DELAY = 0.005

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')


class PgDatabaseWrapper:
    def __init__(self, conn):
        self._conn = conn
        self._conn.autocommit = True
        cursor = conn.cursor()
        with contextlib.closing(cursor):
            cursor.execute(LIST_TABLES_SQL)
            self._tables = [table[0] for table in cursor]

    @property
    def conn(self):
        return self._conn

    def cursor(self):
        return self._conn.cursor()

    def apply_queries(self, queries):
        cursor = self.cursor()
        with contextlib.closing(cursor):
            self._try_truncate_tables(cursor)
            for query in queries:
                self._apply_query(cursor, query)

    def _try_truncate_tables(self, cursor):
        for _ in range(TRUNCATE_RETRIES):
            try:
                self._truncate_tables(cursor)
                break
            except psycopg2.extensions.TransactionRollbackError as exc:
                logger.warning('Truncate table failed: %r', exc)
                time.sleep(TRUNCATE_RETRY_DELAY)
        else:
            self._truncate_tables(cursor)

    def _truncate_tables(self, cursor):
        if self._tables:
            cursor.execute(
                TRUNCATE_SQL_TEMPLATE.format(tables=','.join(self._tables)),
            )

    @staticmethod
    def _apply_query(cursor, query):
        if isinstance(query, str):
            queries = [query]
        elif isinstance(query, (list, tuple)):
            queries = query
        else:
            raise exceptions.PostgresqlError(
                'sql queries of type %s are not supported' % type(query),
            )
        for query_str in queries:
            cursor.execute(query_str)


class PgControl:
    def __init__(self, base_connstr: str, *, verbose: int):
        self._base_connstr = base_connstr
        self._connections: typing.Dict[str, PgDatabaseWrapper] = {}
        self._psql_helper = _get_psql_helper()
        self._pgmigrate = _get_pgmigrate()
        self._verbose = verbose
        self._created_databases: typing.Dict[str, typing.Set[str]] = {}

    @testsuite_utils.cached_property
    def connection(self):
        """Connection to 'postgres' database."""
        connection = self._create_connection('postgres')
        connection.autocommit = True
        return connection

    def create_database(self, dbname):
        if dbname in self._created_databases:
            return
        cursor = self.connection.cursor()
        with contextlib.closing(cursor):
            cursor.execute(DROP_DATABASE_TEMPLATE.format(dbname))
            cursor.execute(CREATE_DATABASE_TEMPLATE.format(dbname))
            self._created_databases[dbname] = set()

    def get_applied_schemas(self, dbname):
        return self._created_databases.get(dbname, set())

    def get_connection_string(self, database: str):
        return utils.connstr_replace_dbname(self._base_connstr, database)

    def get_connection_cached(self, dbname):
        if dbname not in self._connections:
            self._connections[dbname] = PgDatabaseWrapper(
                self._create_connection(dbname),
            )
        return self._connections[dbname]

    def run_script(self, dbname, path):
        command = [
            self._psql_helper,
            '-q',
            '-d',
            self.get_connection_string(dbname),
            '-v',
            'ON_ERROR_STOP=1',
            '-f',
            path,
        ]
        shell.execute(
            command, verbose=self._verbose, command_alias='pgsql/script',
        )

    def run_migrations(self, dbname, path):
        command = [
            self._pgmigrate,
            '-c',
            self.get_connection_string(dbname),
            '-d',
            path,
            '-t',
            'latest',
            '-v',
            'migrate',
        ]
        shell.execute(
            command, verbose=self._verbose, command_alias='pgsql/migrations',
        )

    def _create_connection(self, dbname):
        return psycopg2.connect(self.get_connection_string(dbname))


def _get_psql_helper():
    return os.path.join(utils.SCRIPTS_DIR, 'psql-helper')


def _get_pgmigrate():
    return os.path.join(utils.SCRIPTS_DIR, 'pgmigrate-helper')
