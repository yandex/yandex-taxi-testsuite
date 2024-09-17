import pytest

from . import service
from . import classes


def pytest_addoption(parser):
    group = parser.getgroup('kafka')
    group.addoption('--kafka')
    group.addoption(
        '--no-kafka',
        help='Disable use of Kafka',
        action='store_true',
    )


def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'kafka: per-test Kafka initialization',
    )


def pytest_service_register(register_service):
    register_service('kafka', service.create_kafka_service)


@pytest.fixture
def kafka_producer(
    _kafka_service, _kafka_service_settings, event_loop
) -> classes.KafkaProducer:
    producer = classes.KafkaProducer(
        enabled=_kafka_service, server_port=_kafka_service_settings.server_port
    )
    event_loop.run_until_complete(producer.start())
    yield producer
    event_loop.run_until_complete(producer.teardown())


@pytest.fixture
def kafka_consumer(
    _kafka_service, _kafka_service_settings, event_loop
) -> classes.KafkaConsumer:
    consumer = classes.KafkaConsumer(
        enabled=_kafka_service, server_port=_kafka_service_settings.server_port
    )
    event_loop.run_until_complete(consumer.start())
    yield consumer
    event_loop.run_until_complete(consumer.teardown())


@pytest.fixture(scope='session')
def kafka_disabled(pytestconfig) -> bool:
    return pytestconfig.option.no_kafka


@pytest.fixture(scope='session')
def _kafka_service_settings() -> service.ServiceSettings:
    return service.get_service_settings()


@pytest.fixture(scope='session')
def _kafka_service(
    ensure_service_started,
    kafka_disabled,
    pytestconfig,
    _kafka_service_settings,
) -> bool:
    if kafka_disabled:
        return False
    if not pytestconfig.option.kafka:
        ensure_service_started('kafka', settings=_kafka_service_settings)
    return True
