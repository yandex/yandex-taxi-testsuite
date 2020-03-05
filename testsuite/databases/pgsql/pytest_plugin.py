import collections
import os
import re

import psycopg2
import pytest

from testsuite.environment import service

from . import control
from . import exceptions
from . import utils

DB_FILE_RE_PATTERN = re.compile(r'/pg_(?P<pg_db_alias>\w+)(/?\w*)\.sql$')

DEFAULT_PORT = 5433


class ServiceLocalConfig:
    def __init__(self, databases, base_connstr):
        self.databases = databases
        self._base_connstr = base_connstr
        self._dbindex = {}
        for database in databases:
            self._dbindex[database.dbname] = database
        self._initialized = False
        self._connections = {}

    def initialize(self, pgsql_control):
        if self._initialized:
            return self._connections
        for database in self.databases:
            connections = database.initialize(pgsql_control)
            self._connections.update(connections)
        self._initialized = True
        return self._connections

    def get_connection_string(self, dbname: str, shard: int = 0):
        """Returns connections string for database ``dbname``."""
        try:
            database = self._dbindex[dbname]
        except KeyError:
            raise RuntimeError(f'Unknown database f{dbname}')
        if shard < 0 or shard >= len(database.shards):
            raise RuntimeError(
                f'Database f{dbname} does not have shard {shard}',
            )
        return utils.connstr_replace_dbname(
            self._base_connstr, database.shards[shard].dbname,
        )


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


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'pgsql: per-test PostgreSQL initialization',
    )


def pytest_service_register(register_service):
    @register_service('postgresql')
    def _create_service(
            service_name, working_dir, port=DEFAULT_PORT, env=None,
    ):
        return service.ScriptService(
            service_name=service_name,
            script_path=os.path.join(utils.SCRIPTS_DIR, 'service-postgresql'),
            working_dir=working_dir,
            environment={
                'POSTGRESQL_TMPDIR': working_dir,
                'POSTGRESQL_CONFIGS_DIR': utils.CONFIGS_DIR,
                'POSTGRESQL_PORT': str(port),
                **(env or {}),
            },
            check_ports=[port],
        )


@pytest.fixture
def pgsql(_pgsql, pgsql_apply):
    """Returns pgsql wrapper dictionary.

    Example usage:

    .. code-block:: python

      def test_pg(pgsql):
          cursor = pgsql['example_db'].cursor()
          cursor.execute('SELECT ... FROM ...WHERE ...')
          assert list(cusror) == [...]
    """
    return _pgsql


@pytest.fixture(scope='session')
def pgsql_local_create(postgresql_base_connstr):
    """Creates pgsql configuration.

    :param databases: List of databases.
    :returns: :py:class:`ServiceLocalConfig` instance.
    """

    def _pgsql_local_create(databases):
        return ServiceLocalConfig(databases, postgresql_base_connstr)

    return _pgsql_local_create


@pytest.fixture(scope='session')
def pgsql_disabled(pytestconfig):
    return pytestconfig.option.no_postgresql


@pytest.fixture
def pgsql_local(pgsql_local_create):
    """Configures local pgsql instance.

    :returns: :py:class:`ServiceLocalConfig` instance.

    In order to use pgsql fixture you have to override pgsql_local()
    in your local conftest.py file, example:

    .. code-block:: python

        @pytest.fixture(scope='session')
        def pgsql_local(pgsql_local_create):
            databases = discover.find_databases(
                'service_name', PG_SCHEMAS_PATH)
            return pgsql_local_create(list(databases.values()))
    """
    return pgsql_local_create([])


@pytest.fixture
def _pgsql(_pgsql_service, pgsql_local, pgsql_control, pgsql_disabled):
    if pgsql_disabled:
        pgsql_local = ServiceLocalConfig([], '')

    return pgsql_local.initialize(pgsql_control)


@pytest.fixture
def pgsql_apply(request, _pgsql, load, get_directory_path, mockserver_info):
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

    def _pgsql_default_queries(dbname):
        queries = []
        try:
            queries.append(_substitute_mockserver(load('pg_%s.sql' % dbname)))
        except FileNotFoundError:
            pass
        try:
            queries.extend(
                _pgsql_scan_directory(get_directory_path('pg_%s' % dbname)),
            )
        except FileNotFoundError:
            pass
        return queries

    def _pgsql_mark(dbname, files=(), directories=(), queries=()):
        result_queries = []
        for path in files:
            result_queries.append(_substitute_mockserver(load(path)))
        for path in directories:
            result_queries.extend(
                _pgsql_scan_directory(get_directory_path(path)),
            )
        result_queries.extend(queries)
        return dbname, result_queries

    def _pgsql_scan_directory(root):
        result = []
        for path in utils.scan_sql_directory(root):
            with path.open() as fp:
                result.append(_substitute_mockserver(fp.read()))
        return result

    def _substitute_mockserver(str_val: str):
        return str_val.replace(
            '$mockserver',
            'http://{}:{}'.format(mockserver_info.host, mockserver_info.port),
        )

    overrides = collections.defaultdict(list)
    for mark in request.node.iter_markers('pgsql'):
        dbname, queries = _pgsql_mark(*mark.args, **mark.kwargs)
        if dbname not in _pgsql:
            raise exceptions.PostgresqlError('Unknown database %s' % (dbname,))
        overrides[dbname].extend(queries)

    for dbname, pg_db in _pgsql.items():
        if dbname in overrides:
            queries = overrides[dbname]
        else:
            queries = _pgsql_default_queries(dbname)
        pg_db.apply_queries(queries)


@pytest.fixture
def _pgsql_service(
        pytestconfig,
        pgsql_disabled,
        ensure_service_started,
        pgsql_local,
        _pgsql_port,
):
    if (
            not pgsql_disabled
            and pgsql_local.databases
            and not pytestconfig.option.postgresql
    ):
        ensure_service_started('postgresql', port=_pgsql_port)


@pytest.fixture(scope='session')
def _pgsql_port(worker_id, get_free_port):
    if worker_id == 'master':
        return DEFAULT_PORT
    return get_free_port()


@pytest.fixture(scope='session')
def postgresql_base_connstr(request, _pgsql_port):
    connstr = request.config.option.postgresql
    if not connstr:
        return _get_connection_string(_pgsql_port)
    return _build_base_connstr(connstr)


@pytest.fixture(scope='session')
def pgsql_control(pytestconfig, postgresql_base_connstr, pgsql_disabled):
    if pgsql_disabled:
        return {}
    return control.PgControl(
        postgresql_base_connstr, verbose=pytestconfig.option.verbose,
    )


def _build_base_connstr(connection_string):
    if connection_string.startswith('postgresql://'):
        if not connection_string.endswith('/'):
            raise RuntimeError(
                'PostgreSQL connection string is missing trailing slash',
            )
        return connection_string
    parts = []
    dbname_part = 'dbname='
    for part in connection_string.split():
        if part.startswith('dbname='):
            dbname_part = part
        else:
            parts.append(part)
    parts.append(dbname_part)
    return ' '.join(parts)


def _load_sqlconfig(connection_string):
    return control.PgDatabaseWrapper(psycopg2.connect(connection_string))


def _get_connection_string(port):
    return f'postgresql://testsuite@localhost:{port}/'
