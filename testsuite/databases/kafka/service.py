import os
import pathlib
import typing

from . import classes

from testsuite.environment import service
from testsuite.environment import utils

DEFAULT_SERVER_HOST = 'localhost'
DEFAULT_SERVER_PORT = 9099
DEFAULT_CONTROLLER_PORT = 9100

PLUGIN_DIR = pathlib.Path(__file__).parent
SERVICE_SCRIPT_DIR = PLUGIN_DIR.joinpath('scripts/service-kafka')


def _stringify_start_topics(start_topics: typing.Dict[str, int]) -> str:
    return ';'.join(
        [
            f'{topic}:{partitions_count}'
            for topic, partitions_count in start_topics.items()
        ]
    )


def _parse_custom_topics(custom_topics: str) -> typing.Dict[str, int]:
    if not custom_topics:
        return {}

    result: typing.Dict[str, int] = {}
    for topic_partitions_pair in custom_topics.split(','):
        topic, partition = topic_partitions_pair.split(':')
        result[topic] = int(partition)

    return result


def try_get_custom_topics() -> typing.Dict[str, int]:
    return _parse_custom_topics(
        os.environ.get('TESTSUITE_KAFKA_CUSTOM_TOPICS', '')
    )


def create_kafka_service(
    service_name: str,
    working_dir: str,
    settings: typing.Optional[classes.ServiceSettings] = None,
    env: typing.Optional[typing.Dict[str, str]] = None,
):
    if settings is None:
        settings = get_service_settings()

    return service.ScriptService(
        service_name=service_name,
        script_path=str(SERVICE_SCRIPT_DIR),
        working_dir=working_dir,
        environment={
            'KAFKA_TMPDIR': working_dir,
            'KAFKA_SERVER_HOST': settings.server_host,
            'KAFKA_SERVER_PORT': str(settings.server_port),
            'KAFKA_CONTROLLER_PORT': str(settings.controller_port),
            'KAFKA_START_TOPICS': _stringify_start_topics(
                settings.custom_start_topics or try_get_custom_topics()
            ),
            **(env or {}),
        },
        check_ports=[settings.server_port, settings.controller_port],
        start_timeout=utils.getenv_float(
            key='TESTSUITE_KAFKA_SERVER_START_TIMEOUT',
            default=10.0,
        ),
    )


def get_service_settings(
    custom_start_topics: typing.Dict[str, int] = {},
) -> classes.ServiceSettings:
    return classes.ServiceSettings(
        server_host=utils.getenv_str(
            'TESTSUITE_KAFKA_SERVER_HOST', DEFAULT_SERVER_HOST
        ),
        server_port=utils.getenv_int(
            'TESTSUITE_KAFKA_SERVER_PORT',
            DEFAULT_SERVER_PORT,
        ),
        controller_port=utils.getenv_int(
            'TESTSUITE_KAFKA_CONTROLLER_PORT',
            DEFAULT_CONTROLLER_PORT,
        ),
        custom_start_topics=custom_start_topics,
    )
