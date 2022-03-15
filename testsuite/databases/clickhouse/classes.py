import dataclasses
import pathlib
import typing


@dataclasses.dataclass(frozen=True)
class ConnectionInfo:
    """Clickhouse connection parameters"""

    host: str
    tcp_port: int
    http_port: int
    dbname: typing.Optional[str] = None

    def replace(self, **kwargs) -> 'ConnectionInfo':
        """Returns new instance with attrs updated"""
        return dataclasses.replace(self, **kwargs)


@dataclasses.dataclass(frozen=True)
class DatabaseConfig:
    dbname: str
    migrations: typing.List[pathlib.Path]


DatabasesDict = typing.Dict[str, DatabaseConfig]
