from unittest import mock
 
import pytest
 
from testsuite.databases.rabbitmq import service
 
@pytest.mark.parametrize('worker_suffix', ['worker-a', 'worker-b'])
def test_rabbitmq_service_preserves_worker_environment(tmp_path, worker_suffix):
    settings = service.ServiceSettings(tcp_port=18672, epmd_port=18673)
    env = {
        'WORKER_SUFFIX': worker_suffix,
        'TESTSUITE_DEBUG': '1',
        'RABBITMQ_TMPDIR': 'overridden-directory',
        'RABBITMQ_TCP_PORT': '1',
        'RABBITMQ_EPMD_PORT': '2',
    }
    original_env = env.copy()
 
    with mock.patch.object(service.service, 'ScriptService') as script_service:
        service.create_rabbitmq_service('rabbitmq', tmp_path, settings=settings, env=env)
 
    assert script_service.call_args.kwargs['environment'] == {
        'WORKER_SUFFIX': worker_suffix,
        'TESTSUITE_DEBUG': '1',
        'RABBITMQ_TMPDIR': tmp_path,
        'RABBITMQ_TCP_PORT': str(settings.tcp_port),
        'RABBITMQ_EPMD_PORT': str(settings.epmd_port),
    }
    assert env == original_env
