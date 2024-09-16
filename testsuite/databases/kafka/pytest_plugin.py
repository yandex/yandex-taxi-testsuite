import confluent_kafka
import logging
import pytest

from . import service


logger = logging.getLogger(__name__)


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


def _callback(err, msg):
    if err is not None:
        logger.error(
            f'Failed to deliver message to topic {msg.topic()}: {str(err)}',
        )
    else:
        logger.info(
            f'Message produced to topic {msg.topic()} with key {msg.key()}',
        )


@pytest.fixture
def kafka_producer(_kafka_service, _kafka_service_settings):
    class Wrapper:
        def __init__(self):
            self.producer = confluent_kafka.Producer(
                {
                    'bootstrap.servers': f'localhost:{_kafka_service_settings.server_port}',
                }
            )

        async def produce(self, topic, key, value, callback=_callback):
            self.producer.produce(
                topic,
                value=value,
                key=key,
                on_delivery=callback,
            )
            self.producer.flush()

    return Wrapper()


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
