import pytest
import redis

from testsuite.databases.redis import service


@pytest.fixture(scope='session')
def _redis_service_settings(pytestconfig):
    return service.get_cluster_service_settings()


def test_cluster_config(
    redisdb: redis.RedisCluster, 
    _redis_service_settings: service.ServiceSettings
):
    cluster_nodes = redisdb.cluster_nodes()

    for node, info in cluster_nodes.items():
        port = int(node.rsplit(':', maxsplit=1)[-1])
        if 'master' in info['flags']:
            assert port in _redis_service_settings.master_ports
        elif 'slave' in info['flags']:
            assert port in _redis_service_settings.slave_ports
        else:
            assert False, 'invalid node state'


def test_cluster_rw(redisdb: redis.RedisCluster):
    assert redisdb.set('foo', b'bar')
    assert redisdb.get('foo') == b'bar'
