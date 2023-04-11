import json

import pytest
import redis as redisdb

from . import service


def pytest_addoption(parser):
    group = parser.getgroup('redis')
    group.addoption('--redis-host', help='Redis host')
    group.addoption('--redis-master-port', type=int, help='Redis master port')
    group.addoption(
        '--redis-sentinel-port',
        type=int,
        help='Redis sentinel port',
    )
    group.addoption(
        '--no-redis',
        help='Do not fill redis storage',
        action='store_true',
    )


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'redis_store: per-test redis initialization',
    )


def pytest_service_register(register_service):
    register_service('redis', service.create_redis_service)


@pytest.fixture(scope='session')
def redis_service(
    pytestconfig,
    ensure_service_started,
    _redis_service_settings,
):
    if not pytestconfig.option.no_redis and not pytestconfig.option.redis_host:
        ensure_service_started('redis', settings=_redis_service_settings)


@pytest.fixture
def redis_store(
    pytestconfig,
    request,
    load_json,
    redis_service,
    _redis_masters,
):
    if pytestconfig.option.no_redis:
        yield
        return

    redis_commands = []

    for mark in request.node.iter_markers('redis_store'):
        store_file = mark.kwargs.get('file')
        if store_file is not None:
            redis_commands_from_file = load_json(
                '%s.json' % store_file,
                object_hook=_json_object_hook,
            )
            redis_commands.extend(redis_commands_from_file)

        if mark.args:
            redis_commands.extend(mark.args)

    redis_db = redisdb.StrictRedis(
        host=_redis_masters[0]['host'],
        port=_redis_masters[0]['port'],
    )

    for redis_command in redis_commands:
        func = getattr(redis_db, redis_command[0])
        func(*redis_command[1:])
    try:
        yield redis_db
    finally:
        redis_db.flushall()


@pytest.fixture
def redis_cluster_store(
        pytestconfig, request, load_json, redis_service, cluster_redis_sentinels,
):
    def _flush_all(redis_db):
        slot_infos = redis_db.cluster('SLOTS')
        masters_hosts = [x[2][:2] for x in slot_infos]
        for host, port in masters_hosts:
            redis_db = redisdb.StrictRedis(host=host, port=port)
            redis_db.flushall()
            redis_db.wait(1, 10)
                

    # Wrapper for cluster redis. Process MOVED responses
    class ClusterWrapper:
        def __init__(self, endpoint=None):
            self.end_point = endpoint

        def __getattr__(self, attr):
            def _f(*args, **kwargs):
                try:
                    return self.end_point.__getattribute__(attr)(*args, **kwargs)
                except redisdb.ResponseError as e:
                    resp = e.args[0].split()
                    if resp[0] == 'MOVED':
                        host, port = resp[2].rsplit(':', 1)
                        print(f'redirect to {host}:{port}')
                        c = redisdb.StrictRedis(host=host, port=port)
                        return c.__getattribute__(attr)(*args, **kwargs)
                    else:
                        raise
            return _f

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

    redis_db = ClusterWrapper(
        redisdb.StrictRedis(host=cluster_redis_sentinels[0]['host'],
                            port=cluster_redis_sentinels[0]['port'],
        )
    )

    for redis_command in redis_commands:
        func = getattr(redis_db, redis_command[0])
        func(*redis_command[1:])
    try:
        yield redis_db
    finally:
        _flush_all(redis_db)


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
def cluster_redis_sentinels(pytestconfig, _redis_service_settings):
    # # TODO: WHERE IT COMES FROM???
    # # TODO: IS IT NEEDED AT ALL
    # if pytestconfig.option.redis_host:
    #     # external Redis instance
    #     return [
    #         {
    #             'host': pytestconfig.option.redis_host,
    #             'port': (
    #                 pytestconfig.option.redis_sentinel_port
    #                 or _redis_service_settings.cluster_sentinel_port
    #             ),
    #         },
    #     ]
    return [
        {
            'host': _redis_service_settings.host,
            'port': _redis_service_settings.cluster_sentinel_port,
        },
    ]

@pytest.fixture(scope='session')
def _redis_service_settings():
    return service.get_service_settings()


def _json_object_hook(dct):
    if '$json' in dct:
        return json.dumps(dct['$json'])
    return dct
