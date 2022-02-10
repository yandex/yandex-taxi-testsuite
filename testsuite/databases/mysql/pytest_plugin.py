import collections
import typing

import pytest

from . import classes
from . import control
from . import service
from . import utils


def pytest_addoption(parser):
    """
    :param parser: pytest's argument parser
    """
    group = parser.getgroup('mysql')
    group.addoption('--mysql')
    group.addoption(
        '--no-mysql', help='Disable use of MySQL', action='store_true',
    )


def pytest_configure(config):
    config.addinivalue_line('markers', 'mysql: per-test MySQL initialization')


def pytest_service_register(register_service):
    register_service('mysql', service.create_service)


@pytest.fixture
def mysql(_mysql, _mysql_apply) -> typing.Dict[str, control.ConnectionWrapper]:
    """MySQL fixture.

    Returns dictionary where key is database alias and value is
    :py:class:`control.ConnectionWrapper`
    """
    return _mysql.get_wrappers()


@pytest.fixture(scope='session')
def mysql_disabled(pytestconfig) -> bool:
    return pytestconfig.option.no_mysql


@pytest.fixture(scope='session')
def mysql_conninfo(pytestconfig, _mysql_service_settings):
    if pytestconfig.option.mysql:
        return service.parse_connection_url(pytestconfig.option.mysql)
    return _mysql_service_settings.get_conninfo()


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
        load,
        get_file_path,
        get_directory_path,
        request,
):
    def load_default_queries(dbname):
        queries = []
        try:
            queries.append(
                load_mysql_query(f'my_{dbname}.sql', 'mysql.default_queries'),
            )
        except FileNotFoundError:
            pass
        try:
            queries.extend(
                load_mysql_queries(f'my_{dbname}', 'mysql.default_queries'),
            )
        except FileNotFoundError:
            pass
        return queries

    def mysql_mark(dbname, *, files=(), directories=(), queries=()):
        result_queries = []
        for path in files:
            result_queries.append(load_mysql_query(path, 'mark.mysql.files'))
        for path in directories:
            result_queries.extend(
                load_mysql_queries(path, 'mark.mysql.directories'),
            )
        for query in queries:
            result_queries.append(
                control.MysqlQuery(
                    body=query, source='mark.mysql.queries', path=None,
                ),
            )
        return dbname, result_queries

    def load_mysql_query(path, source):
        return control.MysqlQuery(
            body=load(path), source=source, path=str(get_file_path(path)),
        )

    def load_mysql_queries(directory, source):
        result = []
        for path in utils.scan_sql_directory(get_directory_path(directory)):
            result.append(load_mysql_query(path, source))
        return result

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
        control.apply_queries(
            _mysql_state.wrapper_for(dbconfig.dbname),
            queries,
            keep_tables=dbconfig.keep_tables,
            truncate_non_empty=dbconfig.truncate_non_empty,
        )


@pytest.fixture(scope='session')
def _mysql_service_settings():
    return service.get_service_settings()


@pytest.fixture
def _mysql_service(
        ensure_service_started,
        mysql_local,
        mysql_disabled,
        pytestconfig,
        _mysql_service_settings,
):
    if not mysql_local or mysql_disabled:
        return False
    if not pytestconfig.option.mysql:
        ensure_service_started('mysql', settings=_mysql_service_settings)
    return True


@pytest.fixture(scope='session')
def _mysql_state(pytestconfig, mysql_conninfo):
    return control.DatabasesState(
        connections=control.ConnectionCache(mysql_conninfo),
        verbose=pytestconfig.option.verbose,
    )
