import contextlib
import logging
import subprocess
import threading
import typing

logger = logging.getLogger(__name__)


class BaseError(Exception):
    pass


class SubprocessFailed(BaseError):
    pass


def execute(args, *, env=None, verbose: int, command_alias: str) -> None:
    buffer: typing.List[str] = []
    lock_process_completion = threading.Lock()
    process_completed = False

    def _capture_output(stream):
        for line in stream:
            try:
                decoded = line.decode('utf-8')
            except UnicodeDecodeError:
                logger.error(
                    'Failed to decode subprocess output',
                    with_exc=True,
                )
                continue
            decoded = decoded.rstrip('\r\n')
            with lock_process_completion:
                if process_completed:
                    # Treat postmortem output from pipe as error.
                    # For example pg_ctl does not close pipe on exit so we may
                    # get output later from a started process.
                    logger.warning('[%s] %s', command_alias, decoded)
                else:
                    if verbose > 1:
                        logger.info('[%s] %s', command_alias, decoded)
                    else:
                        buffer.append(decoded)

    def _do_capture_output(stream):
        with contextlib.closing(stream):
            _capture_output(stream)

    process = subprocess.Popen(
        args,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    thread = threading.Thread(target=_do_capture_output, args=(process.stdout,))
    thread.daemon = True
    thread.start()
    exit_code = process.wait()
    with lock_process_completion:
        process_completed = True
        if exit_code != 0:
            for msg in buffer:
                logger.error('[%s] %s', command_alias, msg)
            logger.error(
                '[%s] subprocess %s exited with code %d',
                command_alias,
                process.args,
                exit_code,
            )

    if exit_code != 0:
        raise SubprocessFailed(
            f'{command_alias} subprocess {process.args!r} '
            f'exited with code {exit_code}',
        )
