import pytest

from . import service


def pytest_addoption(parser):
    group = parser.getgroup('redis')
    group.addoption('--no-redis', help='Do not start redis service', action='store_true')


def pytest_service_register(register_service):
    register_service('redis_cluster', service.create_redis_service)


@pytest.fixture(scope='session')
def redis_service_settings():
    return service.get_service_settings()


@pytest.fixture(scope='session')
def redis_service(pytestconfig, ensure_service_started, redis_service_settings):
    if not pytestconfig.option.no_redis:
        ensure_service_started('redis_cluster', settings=redis_service_settings)
