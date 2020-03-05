import asyncio
import contextlib
import ctypes
import itertools
import signal
import subprocess
import sys


ALLOWED_EXIT_CODES = frozenset([0, -signal.SIGKILL, -signal.SIGINT])
_KNOWN_SIGNALS = {
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


class ExitCodeError(RuntimeError):
    def __init__(self, message, exit_code):
        super(ExitCodeError, self).__init__(message)
        self.exit_code = exit_code


@contextlib.asynccontextmanager
async def spawned(
        args,
        *,
        graceful_shutdown=True,
        allowed_exit_codes=ALLOWED_EXIT_CODES,
        **kwargs,
):
    kwargs['preexec_fn'] = kwargs.get('preexec_fn', _setup_process)
    process = subprocess.Popen(args, **kwargs)
    try:
        yield process
    finally:
        for sig in _shutdown_signals(graceful_shutdown):
            retcode = process.poll()
            if retcode is not None:
                if retcode not in allowed_exit_codes:
                    raise _exit_code_error(retcode)
                break
            try:
                process.send_signal(sig)
            except OSError:
                continue
            await asyncio.sleep(0.1)


def _exit_code_error(retcode):
    if retcode >= 0:
        return ExitCodeError(
            'Daemon exited with status code %d' % (retcode,), retcode,
        )

    return ExitCodeError(
        'Daemon was killed by %s signal' % (_pretty_signal(-retcode),),
        retcode,
    )


def _pretty_signal(signal):
    return _KNOWN_SIGNALS.get(signal, signal)


def _shutdown_signals(graceful=False):
    if graceful:
        return itertools.chain(
            itertools.repeat(signal.SIGINT, 100),
            itertools.repeat(signal.SIGKILL),
        )
    return itertools.repeat(signal.SIGKILL)


# Send SIGKILL to child process on unexpected parent termination
if sys.platform == 'linux':
    _PR_SET_PDEATHSIG = 1
    _LIBC = ctypes.CDLL('libc.so.6')

    def _setup_process():
        _LIBC.prctl(_PR_SET_PDEATHSIG, signal.SIGKILL)


else:
    _setup_process = None  # pylint: disable=invalid-name
