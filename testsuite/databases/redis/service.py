import os
import pathlib
import socket
import typing
import warnings

from testsuite.environment import service
from testsuite.environment import utils

from . import genredis

DEFAULT_MASTER_PORTS = (16379, 16389)
DEFAULT_SENTINEL_PORT = 26379
DEFAULT_SLAVE_PORTS = (16380, 16381, 16390)

CLUSTER_MASTER_PORTS = (7000, 7001, 7002)
CLUSTER_SLAVE_PORTS = (7003, 7004, 7005)


class BaseError(Exception):
    pass


class NotEnoughPorts(BaseError):
    pass


class ServiceSettings(typing.NamedTuple):
    host: str
    master_ports: typing.Tuple[int, ...]
    slave_ports: typing.Tuple[int, ...]
    sentinel_port: int
    cluster_mode: bool

    def validate(self):
        if self.cluster_mode:
            if len(self.master_ports) < 3:
                raise NotEnoughPorts('Need at least three master ports')
            if len(self.master_ports) != len(self.slave_ports):
                raise NotEnoughPorts(
                    'Number of slave ports does not match the number of master ports'
                )
        else:
            if len(self.master_ports) != len(DEFAULT_MASTER_PORTS):
                raise NotEnoughPorts(
                    f'Need exactly {len(DEFAULT_MASTER_PORTS)} masters!',
                )
            if len(self.slave_ports) != len(DEFAULT_SLAVE_PORTS):
                raise NotEnoughPorts(
                    f'Need exactly {len(DEFAULT_SLAVE_PORTS)} slaves!',
                )


def get_service_settings(cluster_mode: bool = False) -> ServiceSettings:
    return ServiceSettings(
        host=_get_hostname(),
        master_ports=utils.getenv_ints(
            key='TESTSUITE_REDIS_MASTER_PORTS', default=DEFAULT_MASTER_PORTS,
        ),
        sentinel_port=utils.getenv_int(
            key='TESTSUITE_REDIS_SENTINEL_PORT', default=DEFAULT_SENTINEL_PORT,
        ),
        slave_ports=utils.getenv_ints(
            key='TESTSUITE_REDIS_SLAVE_PORTS', default=DEFAULT_SLAVE_PORTS,
        ),
        cluster_mode=False,
    )


def get_cluster_settings():
    return ServiceSettings(
        host=_get_hostname(),
        master_ports=CLUSTER_MASTER_PORTS,
        slave_ports=CLUSTER_SLAVE_PORTS,
        sentinel_port=0,
        cluster_mode=True,
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
        *settings.master_ports,
        *settings.slave_ports,
    ]
    if not settings.cluster_mode:
        check_ports.append(settings.sentinel_port)

    def prestart_hook():
        configs_dir.mkdir(parents=True, exist_ok=True)
        settings.validate()
        genredis.generate_redis_configs(
            output_path=configs_dir,
            host=settings.host,
            master_ports=settings.master_ports,
            slave_ports=settings.slave_ports,
            sentinel_port=settings.sentinel_port,
            cluster_mode=settings.cluster_mode,
        )

    return service.ScriptService(
        service_name=service_name,
        script_path=str(_get_service_script_path(settings.cluster_mode)),
        working_dir=working_dir,
        environment={
            'REDIS_TMPDIR': working_dir,
            'REDIS_CONFIGS_DIR': str(configs_dir),
            'REDIS_HOST': settings.host,
            'REDIS_MASTER_PORTS': ' '.join(str(p) for p in settings.master_ports),
            'REDIS_SLAVE_PORTS': ' '.join(str(p) for p in settings.slave_ports),
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

def _get_service_script_path(cluster_mode: bool) -> pathlib.Path:
    return pathlib.Path(__file__).parent.joinpath('scripts').joinpath(
        'service-redis-cluster' if cluster_mode else 'service-redis'
    )
