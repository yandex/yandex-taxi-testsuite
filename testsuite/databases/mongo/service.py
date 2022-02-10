import pathlib
import typing

from testsuite.environment import service
from testsuite.environment import utils

from . import connection

DEFAULT_CONFIG_SERVER_PORT = 27118
DEFAULT_MONGOS_PORT = 27217
DEFAULT_SHARD_PORT = 27119

SERVICE_SCRIPT_PATH = pathlib.Path(__file__).parent.joinpath(
    'scripts/service-mongo',
)


class ServiceSettings(typing.NamedTuple):
    config_server_port: int
    mongos_port: int
    shard_port: int

    def get_connection_info(self) -> connection.ConnectionInfo:
        return connection.ConnectionInfo(
            host='localhost', port=self.mongos_port,
        )


def create_mongo_service(
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
            'MONGO_TMPDIR': working_dir,
            'MONGOS_PORT': str(settings.mongos_port),
            'CONFIG_SERVER_PORT': str(settings.config_server_port),
            'SHARD_PORT': str(settings.shard_port),
            **(env or {}),
        },
        check_ports=[
            settings.config_server_port,
            settings.mongos_port,
            settings.shard_port,
        ],
    )


def get_service_settings():
    return ServiceSettings(
        utils.getenv_int(
            key='TESTSUITE_MONGO_CONFIG_SERVER_PORT',
            default=DEFAULT_CONFIG_SERVER_PORT,
        ),
        utils.getenv_int(
            key='TESTSUITE_MONGOS_PORT', default=DEFAULT_MONGOS_PORT,
        ),
        utils.getenv_int(
            key='TESTSUITE_MONGO_SHARD_PORT', default=DEFAULT_SHARD_PORT,
        ),
    )
