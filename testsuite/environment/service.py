import logging
import os
import typing

from . import shell
from . import utils

logger = logging.getLogger(__name__)

_TESTSUITE_LIB_UTILS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'scripts/utils.sh'),
)

COMMAND_START = 'start'
COMMAND_STOP = 'stop'


class ScriptService:
    def __init__(
            self,
            *,
            service_name: str,
            script_path: str,
            working_dir: str,
            check_host: str = 'localhost',
            check_ports: typing.List[int],
            environment: typing.Optional[typing.Dict[str, str]] = None,
            prestart_hook: typing.Optional[typing.Callable] = None,
    ):
        self._service_name = service_name
        self._script_path = script_path
        self._environment = environment
        self._check_host = check_host
        self._check_ports = check_ports
        self._prestart_hook = prestart_hook
        self._started_mark = StartedMark(working_dir)

    def ensure_started(self, *, verbose: int):
        self._started_mark.delete()
        self.stop(verbose=0)
        if self._prestart_hook:
            self._prestart_hook()
        if verbose:
            logger.info('Starting %s service...', self._service_name)
        self._command(COMMAND_START, verbose)
        if verbose:
            logger.info('Service %s started.', self._service_name)
        self._started_mark.create()

    def stop(self, *, verbose: int):
        self._started_mark.delete()
        if verbose:
            logger.info('Stopping %s services...', self._service_name)
        self._command(COMMAND_STOP, verbose)
        if verbose:
            logger.info('Service %s stopped.', self._service_name)

    def is_running(self):
        if not self._started_mark.exists():
            return False
        return all(
            utils.test_tcp_connection(self._check_host, port)
            for port in self._check_ports
        )

    def _command(self, command: str, verbose: int):
        env = os.environ.copy()
        env['TESTSUITE_LIB_UTILS'] = _TESTSUITE_LIB_UTILS
        if self._environment:
            env.update(self._environment)
        args = [self._script_path, command]
        shell.execute(
            args,
            env=env,
            verbose=verbose,
            command_alias=f'env/{self._service_name}/{command}',
        )


class StartedMark:
    def __init__(self, working_dir):
        self._working_dir = working_dir
        self._path = os.path.join(working_dir, '.started')

    def create(self):
        os.makedirs(self._working_dir, exist_ok=True)
        with open(self._path, 'w'):
            pass

    def delete(self):
        try:
            os.remove(self._path)
        except FileNotFoundError:
            pass

    def exists(self):
        return os.path.exists(self._path)
