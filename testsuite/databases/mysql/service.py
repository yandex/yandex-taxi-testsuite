import pathlib
import typing
import urllib.parse

from testsuite.environment import service
from testsuite.environment import utils

from . import classes

DEFAULT_HOSTNAME = 'localhost'
DEFAULT_PORT = 13307

PLUGIN_DIR = pathlib.Path(__file__).parent
SCRIPTS_DIR = PLUGIN_DIR.joinpath('scripts')


def create_service(
        service_name: str,
        working_dir: str,
        settings: typing.Optional[classes.ServiceSettings] = None,
        env: typing.Optional[typing.Dict[str, str]] = None,
):
    if settings is None:
        settings = get_service_settings()
    return service.ScriptService(
        service_name=service_name,
        script_path=str(SCRIPTS_DIR.joinpath('service-mysql')),
        working_dir=working_dir,
        environment={
            'MYSQL_TMPDIR': working_dir,
            'MYSQL_PORT': str(settings.port),
            **(env or {}),
        },
        check_ports=[settings.port],
    )


def get_service_settings():
    return classes.ServiceSettings(
        port=utils.getenv_int(
            key='TESTSUITE_MYSQL_PORT', default=DEFAULT_PORT,
        ),
    )


def parse_connection_url(url: str):
    parts = urllib.parse.urlparse(url)
    if parts.scheme != 'mysql':
        raise RuntimeError(f'Unknown url scheme {parts.scheme}')
    kwargs: dict = {
        key: value
        for value, key in (
            (parts.hostname, 'hostname'),
            (parts.port, 'port'),
            (parts.username, 'user'),
            (parts.password, 'password'),
        )
        if value is not None
    }
    return classes.ConnectionInfo(**kwargs)
