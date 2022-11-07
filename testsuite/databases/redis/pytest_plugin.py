import json

import pytest
import redis as redisdb

from . import service


REDIS_SENTINEL_SERVICE_NAME = 'redis'
REDIS_CLUSTER_SERVICE_NAME = 'redis-cluster'


def pytest_addoption(parser):
    group = parser.getgroup('redis')
    group.addoption('--redis-host', help='Redis host')
    group.addoption('--redis-master-port', type=int, help='Redis master port')
    group.addoption(
        '--redis-sentinel-port', type=int, help='Redis sentinel port',
    )
    group.addoption(
        '--no-redis', help='Do not fill redis storage', action='store_true',
    )
    parser.addini(
        'redis-cluster-mode', type='bool', default=False, help='Redis cluster mode',
    )


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'redis_store: per-test redis initialization',
    )


def pytest_service_register(register_service):
    register_service(
        REDIS_SENTINEL_SERVICE_NAME, service.create_redis_sentinel_service,
    )
    register_service(
        REDIS_CLUSTER_SERVICE_NAME, service.create_redis_cluster_service,
    )


@pytest.fixture(scope='session')
def redis_service(
        pytestconfig, ensure_service_started, _redis_service_settings
):
    if not pytestconfig.option.no_redis and not pytestconfig.option.redis_host:
        if _redis_service_settings.cluster_mode:
            service_name = REDIS_CLUSTER_SERVICE_NAME
        else:
            service_name = REDIS_SENTINEL_SERVICE_NAME
        ensure_service_started(service_name, settings=_redis_service_settings)


@pytest.fixture(scope='session')
def redis_db(redis_service, _redis_service_settings):
    params = {
        'host': _redis_service_settings.host,
        'port': _redis_service_settings.master_ports[0]
    }
    if _redis_service_settings.cluster_mode:
        return redisdb.RedisCluster(**params)
    else:
        return redisdb.StrictRedis(**params)


@pytest.fixture(scope='session')
def redis_sentinel(redis_service, _redis_service_settings):
    return redisdb.StrictRedis(
        host=_redis_service_settings.host,
        port=_redis_service_settings.sentinel_port,
    )


@pytest.fixture
def redis_store(pytestconfig, request, load_json, redis_db):
    if pytestconfig.option.no_redis:
        yield
        return

    redis_commands = []

    for mark in request.node.iter_markers('redis_store'):
        store_file = mark.kwargs.get('file')
        if store_file is not None:
            redis_commands_from_file = load_json(
                '%s.json' % store_file, object_hook=_json_object_hook,
            )
            redis_commands.extend(redis_commands_from_file)

        if mark.args:
            redis_commands.extend(mark.args)

    for redis_command in redis_commands:
        func = getattr(redis_db, redis_command[0])
        func(*redis_command[1:])
    try:
        yield redis_db
    finally:
        redis_db.flushall()


@pytest.fixture(scope='session')
def _redis_masters(pytestconfig, _redis_service_settings):
    if pytestconfig.option.redis_host:
        # external Redis instance
        return [
            {
                'host': pytestconfig.option.redis_host,
                'port': (
                    pytestconfig.option.redis_master_port
                    or _redis_service_settings.master_ports[0]
                ),
            },
        ]
    return [
        {'host': _redis_service_settings.host, 'port': port}
        for port in _redis_service_settings.master_ports
    ]


@pytest.fixture(scope='session')
def redis_sentinels(pytestconfig, _redis_service_settings):
    if pytestconfig.option.redis_host:
        # external Redis instance
        return [
            {
                'host': pytestconfig.option.redis_host,
                'port': (
                    pytestconfig.option.redis_sentinel_port
                    or _redis_service_settings.sentinel_port
                ),
            },
        ]
    return [
        {
            'host': _redis_service_settings.host,
            'port': _redis_service_settings.sentinel_port,
        },
    ]


@pytest.fixture(scope='session')
def _redis_service_settings(pytestconfig):
    if pytestconfig.getini('redis-cluster-mode'):
        return service.get_cluster_service_settings()
    else:
        return service.get_sentinel_service_settings()


def _json_object_hook(dct):
    if '$json' in dct:
        return json.dumps(dct['$json'])
    return dct
