import json
import os

import pytest
import redis as redisdb

from testsuite.environment import service

from . import genredis

DEFAULT_HOST = os.getenv('HOSTNAME', '::1')
MASTERS_DEFAULT_PORTS = (16379, 16389)
SENTINEL_DEFAULT_PORT = 26379
SLAVES_DEFAULT_PORTS = (16380, 16390, 16381)

SERVICE_SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), 'scripts/service-redis',
)


class NotEnoughPorts(Exception):
    pass


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


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'redis_store: per-test redis initialization',
    )


def pytest_service_register(register_service):
    @register_service('redis')
    def _create_redis_service(
            service_name,
            working_dir,
            masters_ports=MASTERS_DEFAULT_PORTS,
            slaves_ports=SLAVES_DEFAULT_PORTS,
            sentinel_port=SENTINEL_DEFAULT_PORT,
            env=None,
    ):
        configs_dir = os.path.join(working_dir, 'configs')
        check_ports = [sentinel_port, *masters_ports, *slaves_ports]

        def prestart_hook():
            os.makedirs(configs_dir, exist_ok=True)
            if len(masters_ports) != len(MASTERS_DEFAULT_PORTS) or len(
                    slaves_ports,
            ) != len(SLAVES_DEFAULT_PORTS):
                raise NotEnoughPorts(
                    'Need exactly %d masters and %d slaves!'
                    % (len(MASTERS_DEFAULT_PORTS), len(SLAVES_DEFAULT_PORTS)),
                )
            genredis.generate_redis_configs(
                output_path=configs_dir,
                host=DEFAULT_HOST,
                master0_port=masters_ports[0],
                master1_port=masters_ports[1],
                slave0_port=slaves_ports[0],
                slave1_port=slaves_ports[1],
                slave2_port=slaves_ports[2],
                sentinel_port=sentinel_port,
            )

        return service.ScriptService(
            service_name=service_name,
            script_path=SERVICE_SCRIPT_PATH,
            working_dir=working_dir,
            environment={
                'REDIS_TMPDIR': working_dir,
                'REDIS_CONFIGS_DIR': configs_dir,
                **(env or {}),
            },
            check_host=DEFAULT_HOST,
            check_ports=check_ports,
            prestart_hook=prestart_hook,
        )


@pytest.fixture(scope='session')
def redis_service(
        pytestconfig,
        ensure_service_started,
        _redis_masters,
        redis_sentinels,
        _redis_slaves,
):
    if not pytestconfig.option.no_redis and not pytestconfig.option.redis_host:
        ensure_service_started(
            'redis',
            masters_ports=[port for _, port in _redis_masters],
            slaves_ports=[port for _, port in _redis_slaves],
            sentinel_port=redis_sentinels[0]['port'],
        )


@pytest.fixture
def redis_store(
        pytestconfig, request, load_json, redis_service, _redis_masters,
):
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

    redis_db = redisdb.StrictRedis(*_redis_masters[0])

    for redis_command in redis_commands:
        func = getattr(redis_db, redis_command[0])
        func(*redis_command[1:])
    try:
        yield redis_db
    finally:
        redis_db.flushall()


@pytest.fixture(scope='session')
def _redis_masters(pytestconfig, worker_id, get_free_port):
    redis_host = pytestconfig.option.redis_host or DEFAULT_HOST
    redis_port = pytestconfig.option.redis_master_port
    if worker_id == 'master':
        ports = list(MASTERS_DEFAULT_PORTS)
    else:
        ports = [get_free_port() for _ in MASTERS_DEFAULT_PORTS]
    if redis_port:
        ports[0] = redis_port
    return [(redis_host, port) for port in ports]


@pytest.fixture(scope='session')
def _redis_slaves(pytestconfig, worker_id, get_free_port):
    redis_host = pytestconfig.option.redis_host or DEFAULT_HOST
    if worker_id == 'master':
        ports = SLAVES_DEFAULT_PORTS
    else:
        ports = [get_free_port() for _ in SLAVES_DEFAULT_PORTS]
    return [(redis_host, port) for port in ports]


@pytest.fixture(scope='session')
def redis_sentinels(pytestconfig, worker_id, _redis_masters, get_free_port):
    redis_host = pytestconfig.option.redis_host or DEFAULT_HOST
    redis_port = pytestconfig.option.redis_sentinel_port
    if worker_id == 'master':
        return [
            {'host': redis_host, 'port': redis_port or SENTINEL_DEFAULT_PORT},
        ]
    return [{'host': redis_host, 'port': redis_port or get_free_port()}]


def _json_object_hook(dct):
    if '$json' in dct:
        return json.dumps(dct['$json'])
    return dct
