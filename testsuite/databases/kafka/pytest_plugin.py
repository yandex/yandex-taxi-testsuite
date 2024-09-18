import typing
import pytest
import os

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
    """
    Per test Kafka producer instance.

    :returns: :py:class:`testsuite.databases.kafka.classes.KafkaProducer`
    """
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
    """
    Per test Kafka consumer instance.

    :returns: :py:class:`testsuite.databases.kafka.classes.KafkaConsumer`
    """
    consumer = classes.KafkaConsumer(
        enabled=_kafka_service, server_port=_kafka_service_settings.server_port
    )
    event_loop.run_until_complete(consumer.start())
    yield consumer
    event_loop.run_until_complete(consumer.teardown())


def _parse_custom_topics(custom_topics: str) -> typing.Dict[str, int]:
    result: typing.Dict[str, int] = {}

    for topic_partitions_pair in custom_topics.split(';'):
        topic, partition = topic_partitions_pair.split(':')
        result[topic] = int(partition)

    return result


@pytest.fixture(scope='session')
def kafka_custom_topics() -> typing.Dict[str, int]:
    """
    Redefine this fixture to pass your custom dictionary of topics' settings.
    """

    custom_topics: str = os.environ.get('TESTSUITE_KAFKA_CUSTOM_TOPICS')
    if custom_topics is None:
        return {}

    return _parse_custom_topics(custom_topics)


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
