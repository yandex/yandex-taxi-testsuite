import dataclasses
import logging
import pathlib
import typing

import pymysql
import pymysql.constants

from testsuite.environment import shell
from testsuite.utils import cached_property

from . import classes
from . import exceptions


logger = logging.getLogger(__name__)

MYSQL_HELPER = pathlib.Path(__file__).parent.joinpath('scripts/mysql-helper')


@dataclasses.dataclass(frozen=True)
class MysqlQuery:
    body: str
    source: str
    path: typing.Optional[str]


class ConnectionWrapper:
    """MySQL database connection wrapper."""

    def __init__(self, connection, conninfo):
        self._connection = connection
        self._conninfo = conninfo

    @property
    def conninfo(self) -> classes.ConnectionInfo:
        """:py:class:`classes.ConnectionInfo` instance."""
        return self._conninfo

    def cursor(self, **kwargs) -> pymysql.cursors.Cursor:
        """Returns cursor instance."""
        return self._connection.cursor(**kwargs)

    def dict_cursor(self, **kwargs) -> pymysql.cursors.Cursor:
        """Return dictionary cursor, pymysql.cursors.DictCursor."""
        kwargs['cursor'] = pymysql.cursors.DictCursor
        return self.cursor(**kwargs)

    def commit(self) -> None:
        self._connection.commit()


class ConnectionCache:
    def __init__(self, conninfo, verbose: bool = False):
        self._conninfo = conninfo
        self._cache: dict = {}
        self._master_connection = None

    def get_master_connection(self):
        if self._master_connection is None:
            self._master_connection = self._connect(self._conninfo)
        return self._master_connection

    def get_conninfo(self, dbname: str) -> classes.ConnectionInfo:
        return self._conninfo.replace(dbname=dbname)

    def get_connection(self, dbname):
        if dbname not in self._cache:
            self._cache[dbname] = self._create_connection(dbname)
        return self._cache[dbname]

    def _create_connection(self, dbname):
        return self._connect(self.get_conninfo(dbname))

    def _connect(self, conninfo: classes.ConnectionInfo):
        return pymysql.connect(
            host=conninfo.hostname,
            port=conninfo.port,
            user=conninfo.user,
            password=conninfo.password,
            database=conninfo.dbname,
            client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS,
        )


class DatabasesState:
    _migrations_run: typing.Set[typing.Tuple[str, str]]
    _initialized: typing.Set[str]

    def __init__(self, connections: ConnectionCache, verbose: bool = False):
        self._connections = connections
        self._verbose = verbose
        self._migrations_run = set()
        self._initialized = set()

    def get_connection(self, dbname: str, create_db: bool = True):
        if dbname not in self._initialized:
            if create_db:
                self._initdb(dbname)
            self._initialized.add(dbname)
        return self._connections.get_connection(dbname)

    def wrapper_for(self, dbname: str):
        return ConnectionWrapper(
            self._connections.get_connection(dbname),
            self._connections.get_conninfo(dbname),
        )

    def run_migration(self, dbname: str, path: str):
        key = dbname, path
        if key in self._migrations_run:
            return
        logger.debug(
            'Running mysql script %s against database %s', path, dbname,
        )
        conninfo = self._connections.get_conninfo(dbname)
        _run_script(conninfo, ['-e', f'source {path}'], verbose=self._verbose)
        self._migrations_run.add(key)

    @cached_property
    def known_databases(self):
        connection = self._connections.get_master_connection()
        cursor = connection.cursor()
        cursor.execute('show databases')
        return {row[0] for row in cursor.fetchall()}

    def _initdb(self, dbname: str):
        connection = self._connections.get_master_connection()
        with connection.cursor() as cursor:
            if dbname in self.known_databases:
                cursor.execute(f'DROP DATABASE IF EXISTS `{dbname}`')
            cursor.execute(f'CREATE DATABASE `{dbname}`')
        connection.commit()
        self._initialized.add(dbname)


class Control:
    def __init__(
            self, databases: classes.DatabasesDict, state: DatabasesState,
    ):
        self._databases = databases
        self._state = state

    def get_wrappers(self):
        return {
            alias: self._state.wrapper_for(dbconfig.dbname)
            for alias, dbconfig in self._databases.items()
        }

    def run_migrations(self):
        for dbconfig in self._databases.values():
            self._run_database_migrations(dbconfig)

    def _run_database_migrations(self, dbconfig):
        self._state.get_connection(dbconfig.dbname, create_db=dbconfig.create)
        for path in dbconfig.migrations:
            self._state.run_migration(dbconfig.dbname, path)


def _build_mysql_args(conninfo: classes.ConnectionInfo) -> typing.List[str]:
    result = ['--protocol=tcp']
    if conninfo.hostname:
        result.append(f'--host={conninfo.hostname}')
    if conninfo.port:
        result.append(f'--port={conninfo.port}')
    if conninfo.user:
        result.append(f'--user={conninfo.user}')
    if conninfo.password:
        result.append(f'--password={conninfo.password}')
    if conninfo.dbname:
        result.append(f'--database={conninfo.dbname}')
    return result


def _run_script(
        conninfo: classes.ConnectionInfo,
        args: typing.List[str],
        verbose: bool,
):
    command = [str(MYSQL_HELPER), *_build_mysql_args(conninfo), *args]
    shell.execute(command, verbose=verbose, command_alias='mysql/script')


def _get_db_tables_list(
        cursor: pymysql.cursors.Cursor,
        db_name: typing.Optional[str],
        truncate_non_empty: bool,
) -> typing.Optional[typing.Tuple]:
    cursor.execute('show tables')
    tables = cursor.fetchall()

    if not db_name:
        return tables

    if truncate_non_empty:
        if tables:
            tables_enum: str = ', '.join([x for (x,) in tables])
            cursor.execute('analyze no_write_to_binlog table ' + tables_enum)
            cursor.execute(
                'select `table_name` from information_schema.tables '
                'where table_rows >= 1 and '
                f'table_schema = \'{db_name}\'',
            )
            tables = cursor.fetchall()
    return tables


def apply_queries(
        connection: ConnectionWrapper,
        queries: typing.List[MysqlQuery],
        keep_tables: typing.List[str] = None,
        truncate_non_empty: bool = False,
):
    if not keep_tables:
        keep_tables = []
    with connection.cursor() as cursor:
        tables = _get_db_tables_list(
            cursor, connection.conninfo.dbname, truncate_non_empty,
        )

        if tables:
            for (table,) in tables:
                if table not in keep_tables:
                    cursor.execute(
                        'set foreign_key_checks=0;'
                        f'truncate table {table};'
                        'set foreign_key_checks=1;',
                    )
        for query in queries:
            try:
                cursor.execute(query.body, args=[])
            except pymysql.Error as exc:
                error_message = (
                    f'MySQL apply query error\n'
                    f'Query from: {query.source}\n'
                )
                if query.path:
                    error_message += f'File path: {query.path}\n'
                error_message += '\n' + str(exc)
                raise exceptions.MysqlError(error_message)
    connection.commit()
