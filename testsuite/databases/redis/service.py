import os
import pathlib
import typing

from testsuite.environment import service
from testsuite.environment import utils

from . import genredis

DEFAULT_MASTER_PORTS = (16379, 16389)
DEFAULT_SENTINEL_PORT = 26379
DEFAULT_SLAVE_PORTS = (16380, 16390, 16381)

SERVICE_SCRIPT_PATH = pathlib.Path(__file__).parent.joinpath(
    'scripts/service-redis',
)


class BaseError(Exception):
    pass


class NotEnoughPorts(BaseError):
    pass


class ServiceSettings(typing.NamedTuple):
    host: str
    master_ports: typing.Tuple[int, ...]
    sentinel_port: int
    slave_ports: typing.Tuple[int, ...]

    def validate(self):
        if len(self.master_ports) != len(DEFAULT_MASTER_PORTS):
            raise NotEnoughPorts(
                f'Need exactly {len(DEFAULT_MASTER_PORTS)} masters!',
            )
        if len(self.slave_ports) != len(DEFAULT_SLAVE_PORTS):
            raise NotEnoughPorts(
                f'Need exactly {len(DEFAULT_SLAVE_PORTS)} slaves!',
            )


def get_service_settings():
    return ServiceSettings(
        os.getenv(key='HOSTNAME', default='::1'),
        utils.getenv_ints(
            key='TESTSUITE_REDIS_MASTER_PORTS', default=DEFAULT_MASTER_PORTS,
        ),
        utils.getenv_int(
            key='TESTSUITE_REDIS_SENTINEL_PORT', default=DEFAULT_SENTINEL_PORT,
        ),
        utils.getenv_ints(
            key='TESTSUITE_REDIS_SLAVE_PORTS', default=DEFAULT_SLAVE_PORTS,
        ),
    )


def create_redis_service(
        service_name,
        working_dir,
        settings: typing.Optional[ServiceSettings] = None,
        env=None,
):
    if settings is None:
        settings = get_service_settings()
    configs_dir = pathlib.Path(working_dir).joinpath('configs')
    check_ports = [
        settings.sentinel_port,
        *settings.master_ports,
        *settings.slave_ports,
    ]

    def prestart_hook():
        configs_dir.mkdir(parents=True, exist_ok=True)
        settings.validate()
        genredis.generate_redis_configs(
            output_path=configs_dir,
            host=settings.host,
            master0_port=settings.master_ports[0],
            master1_port=settings.master_ports[1],
            slave0_port=settings.slave_ports[0],
            slave1_port=settings.slave_ports[1],
            slave2_port=settings.slave_ports[2],
            sentinel_port=settings.sentinel_port,
        )

    return service.ScriptService(
        service_name=service_name,
        script_path=str(SERVICE_SCRIPT_PATH),
        working_dir=working_dir,
        environment={
            'REDIS_TMPDIR': working_dir,
            'REDIS_CONFIGS_DIR': str(configs_dir),
            **(env or {}),
        },
        check_host=settings.host,
        check_ports=check_ports,
        prestart_hook=prestart_hook,
    )
