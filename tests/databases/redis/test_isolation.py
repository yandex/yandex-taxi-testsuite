import pytest
import redis

from testsuite.databases.redis import service


@pytest.mark.redis_standalone_store(['set', 'standalone_key', 'standalone'])
@pytest.mark.redis_cluster_store(['set', 'cluster_key', 'cluster'])
@pytest.mark.redis_store(['set', 'sentinel_key', 'sentinel'])
def test_isolation_rw(
    redis_standalone_store: redis.RedisCluster,
    redis_cluster_store: redis.RedisCluster,
    redis_store: redis.StrictRedis,
):
    assert redis_standalone_store.get('standalone_key') == b'standalone'
    assert redis_standalone_store.get('cluster_key') is None
    assert redis_standalone_store.get('sentinel_key') is None

    assert redis_cluster_store.get('cluster_key') == b'cluster'
    assert redis_cluster_store.get('standalone_key') is None
    assert redis_cluster_store.get('sentinel_key') is None

    assert redis_store.get('sentinel_key') == b'sentinel'
    assert redis_store.get('standalone_key') is None
    assert redis_store.get('cluster_key') is None
