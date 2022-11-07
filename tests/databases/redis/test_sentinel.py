import pytest

from testsuite.databases.redis import service


@pytest.fixture(scope='session')
def _redis_service_settings(pytestconfig):
    return service.get_sentinel_service_settings()


def test_sentinel_basic(
    redis_db: service.ServiceInstances,
    _redis_service_settings: service.ServiceSettings
):
    assert len(redis_db.masters) > 0
    assert len(redis_db.slaves) > 0

    masters = redis_db.sentinel.sentinel_masters()
    assert len(masters) == len(_redis_service_settings.master_ports)
    total_slaves = 0
    for shard, master in masters.items():
        assert master['port'] in _redis_service_settings.master_ports
        assert master['is_master']
        assert not master['is_slave']
        assert not master['is_sentinel']
        assert not master['is_disconnected']

        for slave in redis_db.sentinel.sentinel_slaves(shard):
            assert slave['port'] in _redis_service_settings.slave_ports
            assert slave['is_slave']
            assert not slave['is_master']
            assert not slave['is_sentinel']
            assert not slave['is_disconnected']
            total_slaves += 1

    assert total_slaves == len(_redis_service_settings.slave_ports)
