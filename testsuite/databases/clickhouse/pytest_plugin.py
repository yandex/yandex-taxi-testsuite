import collections
import typing

import clickhouse_driver
import pytest

from . import classes
from . import control
from . import service
from . import utils


def pytest_addoption(parser):
    group = parser.getgroup('clickhouse')
    group.addoption('--clickhouse')
    group.addoption(
        '--no-clickhouse',
        help='Disable use of ClickHouse',
        action='store_true',
    )


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'clickhouse: per-test ClickHouse initialization',
    )


def pytest_service_register(register_service):
    register_service('clickhouse', service.create_clickhouse_service)


@pytest.fixture
def clickhouse(
        _clickhouse, _clickhouse_apply,
) -> typing.Dict[str, clickhouse_driver.Client]:
    return _clickhouse.get_connections()


@pytest.fixture
def _clickhouse(clickhouse_local, _clickhouse_service, _clickhouse_state):
    if not _clickhouse_service:
        clickhouse_local = {}
    dbcontrol = control.Control(clickhouse_local, _clickhouse_state)
    dbcontrol.run_migrations()
    return dbcontrol


@pytest.fixture
def _clickhouse_apply(
        clickhouse_local,
        _clickhouse_state,
        load,
        get_file_path,
        get_directory_path,
        request,
):
    def load_default_queries(dbname):
        queries = []
        try:
            queries.append(
                load_clickhouse_query(
                    f'ch_{dbname}.sql', 'clickhouse.default_queries',
                ),
            )
        except FileNotFoundError:
            pass
        try:
            queries.extend(
                load_clickhouse_queries(
                    f'ch_{dbname}', 'clickhouse.default_queries',
                ),
            )
        except FileNotFoundError:
            pass
        return queries

    def clickhouse_mark(dbname, *, files=(), directories=(), queries=()):
        result_queries = []
        for path in files:
            result_queries.append(
                load_clickhouse_query(path, 'mark.clickhouse.files'),
            )
        for path in directories:
            result_queries.extend(
                load_clickhouse_queries(path, 'mark.clickhouse.directories'),
            )
        for query in queries:
            result_queries.append(
                control.ClickhouseQuery(
                    body=query, source='mark.clickhouse.queries', path=None,
                ),
            )

        return dbname, result_queries

    def load_clickhouse_query(path, source):
        return control.ClickhouseQuery(
            body=load(path), source=source, path=str(get_file_path(path)),
        )

    def load_clickhouse_queries(directory, source):
        return [
            load_clickhouse_query(path, source)
            for path in utils.scan_sql_directory(get_directory_path(directory))
        ]

    overrides = collections.defaultdict(list)
    for mark in request.node.iter_markers('clickhouse'):
        dbname, queries = clickhouse_mark(*mark.args, **mark.kwargs)
        if dbname not in clickhouse_local:
            raise RuntimeError(f'Unknown clickhouse database {dbname}')
        overrides[dbname].extend(queries)

    for alias, dbconfig in clickhouse_local.items():
        if alias in overrides:
            queries = overrides[alias]
        else:
            queries = load_default_queries(alias)
        control.apply_queries(
            _clickhouse_state.get_connection(dbconfig.dbname), queries,
        )


@pytest.fixture(scope='session')
def clickhouse_disabled(pytestconfig) -> bool:
    return pytestconfig.option.no_clickhouse


@pytest.fixture(scope='session')
def clickhouse_local() -> classes.DatabasesDict:
    """Use to override databases configuration."""
    return {}


@pytest.fixture(scope='session')
def _clickhouse_service_settings() -> service.ServiceSettings:
    return service.get_service_settings()


@pytest.fixture(scope='session')
def clickhouse_conn_info(_clickhouse_service_settings):
    return _clickhouse_service_settings.get_connection_info()


@pytest.fixture
def _clickhouse_service(
        ensure_service_started,
        clickhouse_local,
        clickhouse_disabled,
        pytestconfig,
        _clickhouse_service_settings,
):
    if not clickhouse_local or clickhouse_disabled:
        return False
    if not pytestconfig.option.clickhouse:
        ensure_service_started(
            'clickhouse', settings=_clickhouse_service_settings,
        )
    return True


@pytest.fixture(scope='session')
def _clickhouse_state(pytestconfig, clickhouse_conn_info):
    return control.DatabasesState(
        connections=control.ConnectionCache(clickhouse_conn_info),
        verbose=pytestconfig.option.verbose,
    )
