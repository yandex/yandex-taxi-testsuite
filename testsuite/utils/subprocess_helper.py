import subprocess
import typing


def sh(
    *args: str,
    nostderr: bool = True,
    shell: bool = False
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
        shell=shell,
    )
    return proc.stdout.strip()
