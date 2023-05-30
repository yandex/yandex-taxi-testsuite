import pytest
import redis

from testsuite.databases.redis import service


def test_cluster_config(
    redis_cluster_store: redis.RedisCluster,
    _redis_service_settings: service.ServiceSettings,
):
    cluster_nodes = redis_cluster_store.cluster_nodes()

    for node, info in cluster_nodes.items():
        port = int(node.rsplit(':', maxsplit=1)[-1])
        assert port in _redis_service_settings.cluster_ports


def test_cluster_rw(redis_cluster_store: redis.RedisCluster):
    assert redis_cluster_store.set('foo', b'bar')
    assert redis_cluster_store.get('foo') == b'bar'
