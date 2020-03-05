import pathlib
import typing
import urllib.parse

_PLUGIN_DIR = pathlib.Path(__file__).parent
PLUGIN_DIR = str(_PLUGIN_DIR)
CONFIGS_DIR = str(_PLUGIN_DIR.joinpath('configs'))
SCRIPTS_DIR = str(_PLUGIN_DIR.joinpath('scripts'))


def scan_sql_directory(root: str) -> typing.List[pathlib.Path]:
    return [
        path
        for path in sorted(pathlib.Path(root).iterdir())
        if path.is_file() and path.suffix == '.sql'
    ]


def connstr_replace_dbname(connstr: str, dbname: str) -> str:
    """Replace dbname in existing connection string."""
    if connstr.endswith(' dbname='):
        return connstr + dbname
    if connstr.startswith('postgresql://'):
        url = urllib.parse.urlparse(connstr)
        url = url._replace(path=dbname)  # pylint: disable=protected-access
        return url.geturl()
    raise RuntimeError(
        f'Unsupported PostgreSQL connection string format {connstr!r}',
    )
