import dataclasses
import os
import pathlib
import typing

from testsuite.environment import service
from testsuite.environment import utils

DEFAULT_SERVER_PORT = 9092
DEFAULT_CONTROLLER_PORT = 9093

PLUGIN_DIR = pathlib.Path(__file__).parent
SERVICE_SCRIPT_DIR = PLUGIN_DIR.joinpath('scripts/service-kafka')


@dataclasses.dataclass(frozen=True)
class ServiceSettings:
    server_port: int
    controller_port: int


def create_kafka_service(
    service_name: str,
    working_dir: str,
    settings: typing.Optional[ServiceSettings] = None,
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
            'KAFKA_HOME': os.getenv('KAFKA_HOME', '/etc/kafka'),
            'KAFKA_SERVER_PORT': str(settings.server_port),
            'KAFKA_CONTROLLER_PORT': str(settings.controller_port),
            **(env or {}),
        },
        check_ports=[settings.server_port, settings.controller_port],
        start_timeout=utils.getenv_float(
            key='TESTSUITE_KAFKA_SERVER_START_TIMEOUT',
            default=10.0,
        ),
    )


def get_service_settings() -> ServiceSettings:
    return ServiceSettings(
        server_port=utils.getenv_int(
            'TESTSUITE_KAFKA_SERVER_PORT',
            DEFAULT_SERVER_PORT,
        ),
        controller_port=utils.getenv_int(
            'TESTSUITE_KAFKA_CONTROLLER_PORT',
            DEFAULT_CONTROLLER_PORT,
        ),
    )
