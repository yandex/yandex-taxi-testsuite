import pytest

import redis as redisdb

from testsuite.databases.redis import service


@pytest.fixture(scope='session')
def _redis_service_settings(pytestconfig):
    return service.get_sentinel_service_settings()


def test_sentinel_basic(redis_service, _redis_service_settings: service.ServiceSettings):
    redis_db = redisdb.StrictRedis(
        host=_redis_service_settings.host, port=_redis_service_settings.sentinel_port,
    )
    masters = redis_db.sentinel_masters()
    assert len(masters) == len(_redis_service_settings.master_ports)
    total_slaves = 0
    for shard, master in masters.items():
        assert master['port'] in _redis_service_settings.master_ports
        assert master['is_master']
        assert not master['is_slave']
        assert not master['is_sentinel']
        assert not master['is_disconnected']

        for slave in redis_db.sentinel_slaves(shard):
            assert slave['port'] in _redis_service_settings.slave_ports
            assert slave['is_slave']
            assert not slave['is_master']
            assert not slave['is_sentinel']
            assert not slave['is_disconnected']
            total_slaves += 1

    assert total_slaves == len(_redis_service_settings.slave_ports)
