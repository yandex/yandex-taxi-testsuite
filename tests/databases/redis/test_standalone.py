import redis


def test_standalone_rw(redis_standalone_store: redis.RedisCluster):
    assert redis_standalone_store.set('foo_standalone', b'bar')
    assert redis_standalone_store.get('foo_standalone') == b'bar'
