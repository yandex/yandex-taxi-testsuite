import pathlib
import typing


def scan_sql_directory(root: pathlib.Path) -> typing.List[pathlib.Path]:
    return [
        entry
        for entry in sorted(root.iterdir())
        if entry.is_file() and entry.suffix == '.sql'
    ]
