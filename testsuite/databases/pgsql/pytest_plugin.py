import collections
import collections.abc
import re
import typing

import pytest

from . import connection
from . import control
from . import discover
from . import exceptions
from . import service
from . import utils

DB_FILE_RE_PATTERN = re.compile(r'/pg_(?P<pg_db_alias>\w+)(/?\w*)\.sql$')


class ServiceLocalConfig(collections.abc.Mapping):
    def __init__(
            self,
            databases: typing.List[discover.PgShardedDatabase],
            pgsql_control: control.PgControl,
            cleanup_exclude_tables: typing.FrozenSet[str],
    ):
        self._initialized = False
        self._pgsql_control = pgsql_control
        self._databases = databases
        self._shard_connections = {
            shard.pretty_name: pgsql_control.get_connection_cached(
                shard.dbname,
            )
            for db in self._databases
            for shard in db.shards
        }
        self._cleanup_exclude_tables = cleanup_exclude_tables

    def __len__(self) -> int:
        return len(self._shard_connections)

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self._shard_connections)

    def __getitem__(self, dbname: str) -> connection.PgConnectionInfo:
        """ Get
        :py:class:`testsuite.databases.pgsql.connection.PgConnectionInfo`
        instance by database name
        """
        return self._shard_connections[dbname].conninfo

    def initialize(self) -> typing.Dict[str, control.ConnectionWrapper]:
        if self._initialized:
            return self._shard_connections

        for database in self._databases:
            self._pgsql_control.initialize_sharded_db(database)
            for shard in database.shards:
                self._shard_connections[shard.pretty_name].initialize(
                    self._cleanup_exclude_tables,
                )

        self._initialized = True
        return self._shard_connections


def pytest_addoption(parser):
    """
    :param parser: pytest's argument parser
    """
    group = parser.getgroup('postgresql')
    group.addoption('--postgresql', help='PostgreSQL connection string')
    group.addoption(
        '--no-postgresql',
        help='Disable use of PostgreSQL',
        action='store_true',
    )
    group.addoption(
        '--postgresql-keep-existing-db',
        action='store_true',
        help=(
            'Keep existing databases with up-to-date schema. By default '
            'testsuite will drop and create anew any existing database when '
            'initializing databases.'
        ),
    )


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'pgsql: per-test PostgreSQL initialization',
    )


def pytest_service_register(register_service):
    register_service('postgresql', service.create_pgsql_service)


@pytest.fixture(scope='session')
def pgsql_cleanup_exclude_tables():
    return frozenset()


@pytest.fixture
def pgsql(_pgsql, pgsql_apply) -> typing.Dict[str, control.PgDatabaseWrapper]:
    """
    Returns str to
    :py:class:`testsuite.databases.pgsql.control.PgDatabaseWrapper` dictionary

    Example usage:

    .. code-block:: python

      def test_pg(pgsql):
          cursor = pgsql['example_db'].cursor()
          cursor.execute('SELECT ... FROM ...WHERE ...')
          assert list(cusror) == [...]
    """
    return {
        dbname: control.PgDatabaseWrapper(connection)
        for dbname, connection in _pgsql.items()
    }


@pytest.fixture(scope='session')
def pgsql_local_create(
        pgsql_control, pgsql_cleanup_exclude_tables,
) -> typing.Callable[
    [typing.List[discover.PgShardedDatabase]], ServiceLocalConfig,
]:
    """Creates pgsql configuration.

    :param databases: List of databases.
    :returns: :py:class:`ServiceLocalConfig` instance.
    """

    def _pgsql_local_create(databases):
        return ServiceLocalConfig(
            databases, pgsql_control, pgsql_cleanup_exclude_tables,
        )

    return _pgsql_local_create


@pytest.fixture(scope='session')
def pgsql_disabled(pytestconfig) -> bool:
    return pytestconfig.option.no_postgresql


@pytest.fixture
def pgsql_local(pgsql_local_create) -> ServiceLocalConfig:
    """Configures local pgsql instance.

    :returns: :py:class:`ServiceLocalConfig` instance.

    In order to use pgsql fixture you have to override pgsql_local()
    in your local conftest.py file, example:

    .. code-block:: python

        @pytest.fixture(scope='session')
        def pgsql_local(pgsql_local_create):
            databases = discover.find_schemas(
                'service_name', [PG_SCHEMAS_PATH])
            return pgsql_local_create(list(databases.values()))

    Sometimes it is desirable to have tests-only database, maybe used in one
    particular test or tests group. This can be achieved by by overriding
    ``pgsql_local`` fixture in your test file:

    .. code-block:: python

        @pytest.fixture
        def pgsql_local(pgsql_local_create):
            databases = discover.find_schemas(
                'testsuite', [pathlib.Path('custom/pgsql/schema/path')])
            return pgsql_local_create(list(databases.values()))

    ``pgsql_local`` provides access to PostgreSQL connection parameters:

    .. code-block:: python

        def get_custom_connection_string(pgsql_local):
            conninfo = pgsql_local['database_name']
            custom_dsn: str = conninfo.replace(options='-c opt=val').get_dsn()
            return custom_dsn
    """
    return pgsql_local_create([])


@pytest.fixture
def _pgsql(
        _pgsql_service, pgsql_local, pgsql_control, pgsql_disabled: bool,
) -> typing.Dict[str, control.ConnectionWrapper]:
    if pgsql_disabled:
        pgsql_local = ServiceLocalConfig(
            [], pgsql_control, pgsql_cleanup_exclude_tables,
        )
    return pgsql_local.initialize()


@pytest.fixture
def pgsql_apply(
        request,
        _pgsql: ServiceLocalConfig,
        load,
        get_file_path,
        get_directory_path,
        mockserver_info,
) -> None:
    """Initialize PostgreSQL database with data.

    By default pg_${DBNAME}.sql and pg_${DBNAME}/*.sql files are used
    to fill PostgreSQL databases.

    Use pytest.mark.pgsql to change this behaviour:

    @pytest.mark.pgsql(
        'foo@0',
        files=[
            'pg_foo@0_alternative.sql'
        ],
        directories=[
            'pg_foo@0_alternative_dir'
        ],
        queries=[
          'INSERT INTO foo VALUES (1, 2, 3, 4)',
        ]
    )
    """

    def pgsql_default_queries(dbname):
        queries = []
        try:
            queries.append(
                load_pg_query(f'pg_{dbname}.sql', 'pgsql.default_queries'),
            )
        except FileNotFoundError:
            pass
        try:
            queries.extend(
                load_pg_queries(f'pg_{dbname}', 'pgsql.default_queries'),
            )
        except FileNotFoundError:
            pass
        return queries

    def pgsql_mark(dbname, files=(), directories=(), queries=()):
        result_queries = []

        for path in files:
            result_queries.append(load_pg_query(path, 'mark.pgsql.files'))
        for path in directories:
            result_queries.extend(
                load_pg_queries(path, 'mark.pgsql.directories'),
            )
        for query in queries:
            queries_str = []
            if isinstance(query, str):
                queries_str = [query]
            elif isinstance(query, (list, tuple)):
                queries_str = query
            else:
                raise exceptions.PostgresqlError(
                    f'sql queries of type {type(query)} are not supported',
                )
            for query_str in queries_str:
                result_queries.append(
                    control.PgQuery(
                        body=query_str, source='mark.pgsql.queries', path=None,
                    ),
                )
        return dbname, result_queries

    def load_pg_query(path, source):
        query = substitute_mockserver(load(path))
        return control.PgQuery(
            body=query, source=source, path=str(get_file_path(path)),
        )

    def load_pg_queries(directory, source):
        result = []
        for path in utils.scan_sql_directory(get_directory_path(directory)):
            result.append(load_pg_query(path, source))
        return result

    def substitute_mockserver(str_val: str):
        return str_val.replace(
            '$mockserver',
            'http://{}:{}'.format(mockserver_info.host, mockserver_info.port),
        )

    overrides: typing.DefaultDict[
        str, typing.List[control.PgQuery],
    ] = collections.defaultdict(list)
    for mark in request.node.iter_markers('pgsql'):
        dbname, queries = pgsql_mark(*mark.args, **mark.kwargs)
        if dbname not in _pgsql:
            raise exceptions.PostgresqlError('Unknown database %s' % (dbname,))
        overrides[dbname].extend(queries)

    for dbname, pg_db in _pgsql.items():
        if dbname in overrides:
            queries = overrides[dbname]
        else:
            queries = pgsql_default_queries(dbname)
        pg_db.apply_queries(queries)


@pytest.fixture
def _pgsql_service(
        pytestconfig,
        pgsql_disabled: bool,
        ensure_service_started,
        pgsql_local: ServiceLocalConfig,
        _pgsql_service_settings,
) -> None:
    if (
            not pgsql_disabled
            and pgsql_local
            and not pytestconfig.option.postgresql
    ):
        ensure_service_started('postgresql', settings=_pgsql_service_settings)


@pytest.fixture(scope='session')
def postgresql_base_connstr(_pgsql_conninfo) -> str:
    """Connection string to PostgreSQL instance used by testsuite.

    Deprecated, use ``pgsql_control`` fixture instead:

    - ``pgsql_local[shard.pretty_name].get_dsn()``
    - ``pgsql_local[shard.pretty_name].get_uri()``
    """
    if _pgsql_conninfo.dbname == '':
        _pgsql_conninfo = _pgsql_conninfo.replace(dbname=None)
    dsn = _pgsql_conninfo.get_dsn()
    if _pgsql_conninfo.dbname is None:
        dsn += ' dbname='
    return dsn


@pytest.fixture(scope='session')
def pgsql_control(pytestconfig, _pgsql_conninfo, pgsql_disabled: bool):
    if pgsql_disabled:
        return {}
    return control.PgControl(
        _pgsql_conninfo,
        verbose=pytestconfig.option.verbose,
        skip_applied_schemas=(
            pytestconfig.option.postgresql_keep_existing_db
            or pytestconfig.option.service_wait
        ),
    )


@pytest.fixture(scope='session')
def _pgsql_service_settings() -> service.ServiceSettings:
    return service.get_service_settings()


@pytest.fixture(scope='session')
def _pgsql_conninfo(
        request, _pgsql_service_settings,
) -> connection.PgConnectionInfo:
    connstr = request.config.option.postgresql
    if connstr:
        return connection.parse_connection_string(connstr)
    return _pgsql_service_settings.get_conninfo()
