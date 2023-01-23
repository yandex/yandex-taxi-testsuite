import subprocess
import typing


def sh(
    *args: str,
    nostderr: bool = True,
) -> str:  # pylint: disable=invalid-name
    stderr: typing.Optional[int]
    if nostderr:
        stderr = subprocess.DEVNULL
    else:
        stderr = None
    proc = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=stderr,
        encoding='utf-8',
        check=True,
    )
    return proc.stdout.strip()
