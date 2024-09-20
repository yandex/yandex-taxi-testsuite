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


@compat.asynccontextmanager
async def _create_producer(enabled: bool, server_port: int):
    producer = classes.KafkaProducer(enabled=enabled, server_port=server_port)
    try:
        await producer.start()
        yield producer
    finally:
        await producer.teardown()


@pytest.fixture(scope='session')
async def kafka_producer(
    _kafka_service, _kafka_service_settings
) -> typing.AsyncGenerator[classes.KafkaProducer, None]:
    """
    Per test Kafka producer instance.

    :returns: :py:class:`testsuite.databases.kafka.classes.KafkaProducer`
    """
    async with _create_producer(
        _kafka_service, _kafka_service_settings.server_port
    ) as producer:
        yield producer


@compat.asynccontextmanager
async def _create_consumer(enabled: bool, server_port: int):
    consumer = classes.KafkaConsumer(enabled=enabled, server_port=server_port)
    try:
        await consumer.start()
        yield consumer
    finally:
        await consumer.teardown()


@pytest.fixture(scope='session')
async def _kafka_consumer_client(
    _kafka_service, _kafka_service_settings
) -> typing.AsyncGenerator[classes.KafkaConsumer, None]:
    async with _create_consumer(
        _kafka_service, _kafka_service_settings.server_port
    ) as consumer:
        yield consumer


@pytest.fixture
async def kafka_consumer(_kafka_consumer_client):
    """
    Per test Kafka consumer instance.

    :returns: :py:class:`testsuite.databases.kafka.classes.KafkaConsumer`
    """
    yield _kafka_consumer_client
    await _kafka_consumer_client._unsubscribe()


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
