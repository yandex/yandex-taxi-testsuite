import typing
import pytest

from . import service
from . import classes

from testsuite.utils import compat


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


@pytest.fixture(scope='session')
async def _kafka_global_producer(
    _kafka_service, _kafka_service_settings
) -> typing.AsyncGenerator[classes.KafkaConsumer, None]:
    producer = classes.KafkaProducer(
        enabled=_kafka_service, server_port=_kafka_service_settings.server_port
    )
    await producer.start()

    async with compat.aclosing(producer):
        yield producer


@pytest.fixture
async def kafka_producer(
    _kafka_global_producer,
) -> typing.AsyncGenerator[classes.KafkaProducer, None]:
    """
    Per test Kafka producer instance.

    :returns: :py:class:`testsuite.databases.kafka.classes.KafkaProducer`
    """
    yield _kafka_global_producer
    await _kafka_global_producer._flush()


@pytest.fixture(scope='session')
async def _kafka_global_consumer(
    _kafka_service, _kafka_service_settings
) -> typing.AsyncGenerator[classes.KafkaConsumer, None]:
    consumer = classes.KafkaConsumer(
        enabled=_kafka_service, server_port=_kafka_service_settings.server_port
    )
    await consumer.start()

    async with compat.aclosing(consumer):
        yield consumer


@pytest.fixture
async def kafka_consumer(_kafka_global_consumer):
    """
    Per test Kafka consumer instance.

    :returns: :py:class:`testsuite.databases.kafka.classes.KafkaConsumer`
    """
    yield _kafka_global_consumer
    await _kafka_global_consumer._unsubscribe()


@pytest.fixture(scope='session')
def kafka_custom_topics() -> typing.Dict[str, int]:
    """
    Redefine this fixture to pass your custom dictionary of topics' settings.
    """

    return service.try_get_custom_topics()


@pytest.fixture(scope='session')
def kafka_disabled(pytestconfig) -> bool:
    return pytestconfig.option.no_kafka


@pytest.fixture(scope='session')
def _kafka_service_settings(kafka_custom_topics) -> service.ServiceSettings:
    return service.get_service_settings(kafka_custom_topics)


@pytest.fixture(scope='session')
def _kafka_service(
    ensure_service_started,
    kafka_disabled,
    pytestconfig,
    _kafka_service_settings,
    kafka_custom_topics,
) -> bool:
    if kafka_disabled:
        return False
    if not pytestconfig.option.kafka:
        ensure_service_started('kafka', settings=_kafka_service_settings)
    return True
