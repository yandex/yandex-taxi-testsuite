import pytest
import redis as redisdb

from testsuite.databases.redis import service


@pytest.fixture(scope='session')
def _redis_service_settings(pytestconfig):
    return service.get_cluster_service_settings()


def test_cluster_basic(redis_service, _redis_service_settings: service.ServiceSettings):
    redis_db = redisdb.StrictRedis(
        host=_redis_service_settings.host,
        port=_redis_service_settings.master_ports[0],
    )
    cluster_nodes = redis_db.cluster('NODES')

    for node, info in cluster_nodes.items():
        port = int(node.rsplit(':', maxsplit=1)[-1])
        if 'master' in info['flags']:
            assert port in _redis_service_settings.master_ports
        elif 'slave' in info['flags']:
            assert port in _redis_service_settings.slave_ports
        else:
            assert False, 'invalid node state'
