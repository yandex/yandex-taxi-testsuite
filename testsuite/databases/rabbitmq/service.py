import pathlib
import typing

from testsuite.environment import service
from testsuite.environment import utils

from . import classes

DEFAULT_RABBITMQ_TCP_PORT = 8672
DEFAULT_RABBITMQ_EPMD_PORT = 8673

SERVICE_SCRIPT_PATH = pathlib.Path(__file__).parent.joinpath(
    'scripts/service-rabbitmq',
)


class ServiceSettings(typing.NamedTuple):
    tcp_port: int
    epmd_port: int

    def get_connection_info(self) -> classes.ConnectionInfo:
        return classes.ConnectionInfo(host='localhost', tcp_port=self.tcp_port)


def create_rabbitmq_service(
        service_name,
        working_dir,
        settings: typing.Optional[ServiceSettings] = None,
        env: typing.Optional[typing.Dict[str, str]] = None,
):
    if settings is None:
        settings = get_service_settings()
    return service.ScriptService(
        service_name=service_name,
        script_path=str(SERVICE_SCRIPT_PATH),
        working_dir=working_dir,
        environment={
            'RABBITMQ_TMPDIR': working_dir,
            'RABBITMQ_TCP_PORT': str(settings.tcp_port),
            'RABBITMQ_EPMD_PORT': str(settings.epmd_port),
            'RABBITMQ_BINDIR': utils.getenv_str(
                key='TESTSUITE_RABBITMQ_BINDIR',
                default='/usr/lib/rabbitmq/bin/',
            ),
        },
        check_ports=[settings.tcp_port, settings.epmd_port],
        start_timeout=utils.getenv_float(
            key='TESTSUITE_RABBITMQ_SERVER_START_TIMEOUT', default=10.0,
        ),
    )


def get_service_settings() -> ServiceSettings:
    return ServiceSettings(
        utils.getenv_int(
            key='TESTSUITE_RABBITMQ_TCP_PORT',
            default=DEFAULT_RABBITMQ_TCP_PORT,
        ),
        utils.getenv_int(
            key='TESTSUITE_RABBITMQ_EPMD_PORT',
            default=DEFAULT_RABBITMQ_EPMD_PORT,
        ),
    )
