import os
import pathlib
import socket
import typing
import warnings

from testsuite.environment import service
from testsuite.environment import utils

from . import genredis

DEFAULT_REDIS_PORT_MIN = 7000
DEFAULT_REDIS_PORT_MAX = 7005

SERVICE_SCRIPT_PATH = pathlib.Path(__file__).parent.joinpath(
    'scripts/service-redis',
)


class SettingsError(Exception):
    pass


class ServiceSettings(typing.NamedTuple):
    host: str
    port_min: int
    port_max: int

    def validate(self):
        if (self.port_max <= self.port_min):
            raise SettingsError(f'Invalid ports range {self.port_min}..{self.port_max}')
        if (self.port_max - self.port_min < 5):
            raise SettingsError(f'Need at least 6 ports')


def get_service_settings():
    return ServiceSettings(
        host=_get_hostname(),
        port_min=utils.getenv_int(
            key='TESTSUITE_REDIS_PORT_MIN', default=DEFAULT_REDIS_PORT_MIN,
        ),
        port_max=utils.getenv_int(
            key='TESTSUITE_REDIS_PORT_MAX', default=DEFAULT_REDIS_PORT_MAX,
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
    check_ports = list(range(settings.port_min, settings.port_max + 1))

    def prestart_hook():
        configs_dir.mkdir(parents=True, exist_ok=True)
        settings.validate()
        genredis.generate_redis_configs(
            output_path=configs_dir,
            host=settings.host,
            port_min=settings.port_min,
            port_max=settings.port_max,
        )

    return service.ScriptService(
        service_name=service_name,
        script_path=str(SERVICE_SCRIPT_PATH),
        working_dir=working_dir,
        environment={
            'REDIS_TMPDIR': working_dir,
            'REDIS_CONFIGS_DIR': str(configs_dir),
            'REDIS_HOST': settings.host,
            'REDIS_PORT_MIN': str(settings.port_min),
            'REDIS_PORT_MAX': str(settings.port_max),
            **(env or {}),
        },
        check_host=settings.host,
        check_ports=check_ports,
        prestart_hook=prestart_hook,
    )


def _get_hostname():
    hostname = 'localhost'
    for var in ('TESTSUITE_REDIS_HOSTNAME', 'HOSTNAME'):
        if var in os.environ:
            hostname = os.environ[var]
            break
    return _resolve_hostname(hostname)


def _resolve_hostname(hostname: str) -> str:
    for family in socket.AF_INET6, socket.AF_INET:
        try:
            result = socket.getaddrinfo(
                hostname, None, family=family, type=socket.SOCK_STREAM,
            )
        except socket.error:
            continue
        if result:
            return result[0][4][0]
    warnings.warn(f'Failed to resolve hostname {hostname}')
    return hostname
