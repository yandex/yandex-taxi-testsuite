import collections
import dataclasses
import os

import pytest

from . import classes, control, service, utils


def pytest_addoption(parser):
    """
    :param parser: pytest's argument parser
    """
    group = parser.getgroup('mysql')
    group.addoption('--mysql')
    group.addoption(
        '--no-mysql',
        help='Disable use of MySQL',
        action='store_true',
    )


def pytest_configure(config):
    config.addinivalue_line('markers', 'mysql: per-test MySQL initialization')


def pytest_service_register(register_service):
    register_service('mysql', service.create_service)


@pytest.fixture
def mysql(_mysql, _mysql_apply) -> dict[str, control.ConnectionWrapper]:
    """MySQL fixture.

    Returns dictionary where key is database alias and value is
    :py:class:`control.ConnectionWrapper`
    """
    return _mysql.get_wrappers()


@pytest.fixture(scope='session')
def mysql_disabled(pytestconfig) -> bool:
    return pytestconfig.option.no_mysql


@pytest.fixture(scope='session')
def mysql_conninfo(pytestconfig, request):
    if pytestconfig.option.mysql:
        return service.parse_connection_url(pytestconfig.option.mysql)
    settings = request.getfixturevalue('_mysql_service_settings')
    return settings.get_conninfo()


@pytest.fixture(scope='session')
def mysql_local() -> classes.DatabasesDict:
    """Use to override databases configuration."""
    return {}


@pytest.fixture
def _mysql(mysql_local, _mysql_service, _mysql_state):
    if not _mysql_service:
        mysql_local = {}
    dbcontrol = control.Control(mysql_local, _mysql_state)
    dbcontrol.run_migrations()
    return dbcontrol


@pytest.fixture
def _mysql_apply(
    mysql_local,
    _mysql_state,
    _mysql_query_loader,
    request,
):
    def load_default_queries(dbname):
        return [
            *_mysql_query_loader.load(
                f'my_{dbname}.sql', 'mysql.default_queries', missing_ok=True
            ),
            *_mysql_query_loader.loaddir(
                f'my_{dbname}', 'mysql.default_queries', missing_ok=True
            ),
        ]

    def mysql_mark(dbname, *, files=(), directories=(), queries=()):
        result_queries = []
        for path in files:
            result_queries += _mysql_query_loader.load(path, 'mark.mysql.files')
        for path in directories:
            result_queries += _mysql_query_loader.loaddir(
                path, 'mark.mysql.directories'
            )
        for query in queries:
            result_queries.append(
                control.MysqlQuery(
                    body=query,
                    source='mark.mysql.queries',
                    path=None,
                ),
            )
        return dbname, result_queries

    overrides = collections.defaultdict(list)

    for mark in request.node.iter_markers('mysql'):
        dbname, queries = mysql_mark(*mark.args, **mark.kwargs)
        if dbname not in mysql_local:
            raise RuntimeError(f'Unknown mysql database {dbname}')
        overrides[dbname].extend(queries)

    for alias, dbconfig in mysql_local.items():
        if alias in overrides:
            queries = overrides[alias]
        else:
            queries = load_default_queries(alias)
        connection_wrapper = _mysql_state.wrapper_for(dbconfig.dbname)
        connection_wrapper.apply_queries(
            queries,
            keep_tables=dbconfig.keep_tables,
            truncate_non_empty=dbconfig.truncate_non_empty,
        )


@pytest.fixture
def _mysql_query_loader(get_file_path, get_directory_path):
    def load_query(path, source):
        return control.MysqlQuery(
            body=path.read_text(),
            source=source,
            path=str(path),
        )

    class Loader:
        @staticmethod
        def load(path, source, missing_ok=False):
            data = get_file_path(path, missing_ok=missing_ok)
            if not data:
                return []
            return [load_query(data, source)]

        @staticmethod
        def loaddir(directory, source, missing_ok=False):
            result = []
            directory = get_directory_path(directory, missing_ok=missing_ok)
            if not directory:
                return []
            for path in utils.scan_sql_directory(directory):
                result.append(load_query(path, source))
            return result

    return Loader()


@pytest.fixture(scope='session')
def mysql_service_settings(request) -> classes.ServiceSettings:
    """Settings for the locally launched MySQL/MariaDB server.

    Allocate a free port unless TESTSUITE_MYSQL_PORT explicitly selects one.
    Override this session-scoped fixture to customize local server settings.
    mysql_conninfo and the launcher use the same settings for local connections.
    With --mysql, the local server is not started and this fixture is not requested.
    """
    settings = service.get_service_settings()
    if 'TESTSUITE_MYSQL_PORT' not in os.environ:
        get_free_port = request.getfixturevalue('get_free_port')
        settings = dataclasses.replace(settings, port=get_free_port())
    return settings


@pytest.fixture(scope='session')
def _mysql_service_settings(mysql_service_settings):
    return mysql_service_settings


@pytest.fixture
def _mysql_service(
    mysql_local,
    mysql_disabled,
    pytestconfig,
    request,
):
    if not mysql_local or mysql_disabled:
        return False
    if not pytestconfig.option.mysql:
        settings = request.getfixturevalue('_mysql_service_settings')
        ensure_service_started = request.getfixturevalue(
            'ensure_service_started'
        )
        ensure_service_started('mysql', settings=settings)
    return True


@pytest.fixture(scope='session')
def _mysql_state(pytestconfig, mysql_conninfo):
    return control.DatabasesState(
        connections=control.ConnectionCache(mysql_conninfo),
        verbose=pytestconfig.option.verbose,
    )
