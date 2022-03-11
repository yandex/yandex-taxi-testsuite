import asyncio
import ctypes
import logging
import signal
import subprocess
import sys
import time
from typing import AsyncGenerator
from typing import Dict
from typing import Sequence

from testsuite.utils import compat

SIGNAL_ERRORS: Dict[int, str] = {
    signal.SIGSEGV: (
        'Service crashed with {signal_name} signal (segmentation fault)'
    ),
    signal.SIGABRT: 'Service aborted by {signal_name} signal',
}
DEFAULT_SIGNAL_ERROR = 'Service terminated by {signal_name} signal'

_KNOWN_SIGNALS: Dict[int, str] = {
    signal.SIGABRT: 'SIGABRT',
    signal.SIGBUS: 'SIGBUS',
    signal.SIGFPE: 'SIGFPE',
    signal.SIGHUP: 'SIGHUP',
    signal.SIGINT: 'SIGINT',
    signal.SIGKILL: 'SIGKILL',
    signal.SIGPIPE: 'SIGPIPE',
    signal.SIGSEGV: 'SIGSEGV',
    signal.SIGTERM: 'SIGTERM',
}
_POLL_TIMEOUT = 0.1

logger = logging.getLogger(__name__)


class ExitCodeError(RuntimeError):
    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@compat.asynccontextmanager
async def spawned(
        args: Sequence[str],
        *,
        shutdown_signal: int = signal.SIGINT,
        shutdown_timeout: float = 120,
        subprocess_spawner=None,
        **kwargs,
) -> AsyncGenerator[subprocess.Popen, None]:
    kwargs['preexec_fn'] = kwargs.get('preexec_fn', _setup_process)
    if subprocess_spawner:
        process = subprocess_spawner(args, **kwargs)
    else:
        process = subprocess.Popen(args, **kwargs)
    try:
        yield process
    finally:
        await _service_shutdown(
            process,
            shutdown_signal=shutdown_signal,
            shutdown_timeout=shutdown_timeout,
        )


async def _service_shutdown(process, *, shutdown_signal, shutdown_timeout):
    allowed_exit_codes = (-shutdown_signal, 0)

    retcode = process.poll()
    if retcode is not None:
        logger.info('Process already finished with code %d', retcode)
        if retcode not in allowed_exit_codes:
            raise _exit_code_error(retcode)
        return retcode

    try:
        process.send_signal(shutdown_signal)
    except OSError:
        pass
    else:
        logger.info(
            'Trying to stop process with signal %s',
            _pretty_signal(shutdown_signal),
        )
        poll_start = time.monotonic()
        while True:
            retcode = process.poll()
            if retcode is not None:
                if retcode not in allowed_exit_codes:
                    raise _exit_code_error(retcode)
                return retcode
            current_time = time.monotonic()
            if current_time - poll_start > shutdown_timeout:
                break
            await asyncio.sleep(_POLL_TIMEOUT)

        logger.warning(
            'Process did not finished within shutdown timeout %d seconds',
            shutdown_timeout,
        )

    logger.warning('Now killing process with signal SIGKILL')
    while True:
        retcode = process.poll()
        if retcode is not None:
            raise _exit_code_error(retcode)
        try:
            process.send_signal(signal.SIGKILL)
        except OSError:
            continue
        await asyncio.sleep(_POLL_TIMEOUT)


def _exit_code_error(retcode: int) -> ExitCodeError:
    if retcode >= 0:
        return ExitCodeError(
            f'Service exited with status code {retcode}', retcode,
        )
    signal_name = _pretty_signal(-retcode)
    signal_error_fmt = SIGNAL_ERRORS.get(-retcode, DEFAULT_SIGNAL_ERROR)
    return ExitCodeError(
        signal_error_fmt.format(signal_name=signal_name), retcode,
    )


def _pretty_signal(signum: int) -> str:
    if signum in _KNOWN_SIGNALS:
        return _KNOWN_SIGNALS[signum]
    return str(signum)


# Send SIGKILL to child process on unexpected parent termination
_PR_SET_PDEATHSIG = 1
if sys.platform == 'linux':
    _LIBC = ctypes.CDLL('libc.so.6')
else:
    _LIBC = None


def _setup_process() -> None:
    if _LIBC is not None:
        _LIBC.prctl(_PR_SET_PDEATHSIG, signal.SIGKILL)
