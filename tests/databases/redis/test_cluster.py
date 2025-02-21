import pytest
import redis

from testsuite.databases.redis import service


def test_cluster_config(
    redis_cluster_store: redis.RedisCluster,
    _redis_cluster_service_settings: service.ClusterServiceSettings,
):
    cluster_nodes = redis_cluster_store.cluster_nodes()

    for node, info in cluster_nodes.items():
        port = int(node.rsplit(':', maxsplit=1)[-1])
        assert port in _redis_cluster_service_settings.cluster_ports


def test_cluster_rw(redis_cluster_store: redis.RedisCluster):
    assert redis_cluster_store.set('foo_cluster', b'bar')
    assert redis_cluster_store.get('foo_cluster') == b'bar'


def test_cluster_replicas(redis_cluster_store: redis.RedisCluster):
    cluster_nodes = redis_cluster_store.cluster_nodes()

    assert redis_cluster_store.get_replicas(), f'No replicas. {cluster_nodes}'

    primary = redis_cluster_store.get_node_from_key(f'key', replica=False)
    assert primary, f'No primary for node. Nodes: {cluster_nodes}'

    replica = redis_cluster_store.get_node_from_key(f'key', replica=True)
    assert replica, f'No replica for node. Nodes: {cluster_nodes}'
