import pytest

from testsuite.databases.redis import service


@pytest.fixture(scope='session')
def _redis_service_settings(pytestconfig):
    return service.get_cluster_service_settings()


def test_cluster_basic(
    redis_db: service.ServiceInstances, 
    _redis_service_settings: service.ServiceSettings
):
    assert len(redis_db.masters) > 0
    assert len(redis_db.slaves) > 0
    assert redis_db.sentinel is None

    redis_master = redis_db.masters[0]
    cluster_nodes = redis_master.cluster('NODES')

    for node, info in cluster_nodes.items():
        port = int(node.rsplit(':', maxsplit=1)[-1])
        if 'master' in info['flags']:
            assert port in _redis_service_settings.master_ports
        elif 'slave' in info['flags']:
            assert port in _redis_service_settings.slave_ports
        else:
            assert False, 'invalid node state'
