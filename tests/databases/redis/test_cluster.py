import pytest
import time

import redis as redisdb

from testsuite.databases.redis import service


CLUSTER_INIT_TIMEOUT = 5.0


@pytest.fixture(scope='session')
def _redis_service_settings(pytestconfig):
    return service.get_cluster_service_settings()


def test_cluster_basic(redis_service, _redis_service_settings: service.ServiceSettings):
    def cluster_nodes():
        redis_db = redisdb.StrictRedis(
            host=_redis_service_settings.host,
            port=_redis_service_settings.master_ports[0],
        )
        return redis_db.cluster('NODES')

    begin = time.time()
    while time.time() - begin < CLUSTER_INIT_TIMEOUT:
        slaves = [n for _, n in cluster_nodes().items() if 'slave' in n['flags']]
        if len(slaves) == len(_redis_service_settings.slave_ports):
            break
    assert time.time() - begin < CLUSTER_INIT_TIMEOUT

    for node, info in cluster_nodes().items():
        port = int(node.rsplit(':', maxsplit=1)[-1])
        if 'master' in info['flags']:
            assert port in _redis_service_settings.master_ports
        elif 'slave' in info['flags']:
            assert port in _redis_service_settings.slave_ports
        else:
            assert False, 'invalid node state'
