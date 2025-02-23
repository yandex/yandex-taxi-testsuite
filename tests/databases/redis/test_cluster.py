import pytest
import redis

from testsuite.databases.redis import service


def test_cluster_config(
    redis_cluster_store: redis.RedisCluster,
    _redis_cluster_service_settings: service.ClusterServiceSettings,
    redis_cluster_replicas: int,
):
    cluster_nodes = redis_cluster_store.cluster_nodes()

    replicas = 0
    masters = 0
    for node, info in cluster_nodes.items():
        port = int(node.rsplit(':', maxsplit=1)[-1])
        assert port in _redis_cluster_service_settings.cluster_ports

        flags_string = str(info['flags'])
        if 'slave' in flags_string or 'replica' in flags_string:
            replicas += 1
        else:
            masters += 1

    assert replicas == masters * redis_cluster_replicas


def test_cluster_rw(redis_cluster_store: redis.RedisCluster):
    assert redis_cluster_store.set('foo_cluster', b'bar')
    assert redis_cluster_store.get('foo_cluster') == b'bar'


def test_cluster_replicas(redis_cluster_store: redis.RedisCluster):
    assert redis_cluster_store.get_replicas(), 'No replicas'

    primary = redis_cluster_store.get_node_from_key('key', replica=False)
    assert primary, 'No primary for key'

    replica = redis_cluster_store.get_node_from_key('key', replica=True)
    assert replica, 'No replica for key'
