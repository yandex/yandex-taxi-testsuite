import collections
import dataclasses
import itertools
import logging
import pathlib
from typing import DefaultDict
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional

from . import exceptions
from . import utils

logger = logging.getLogger(__name__)

SINGLE_SHARD = -1


@dataclasses.dataclass(frozen=True)
class ShardName:
    db_name: str
    shard: int


@dataclasses.dataclass
class ShardFiles:
    name: ShardName
    files: Optional[List[pathlib.Path]] = None
    pg_migrations: Optional[List[pathlib.Path]] = None


@dataclasses.dataclass
class ShardFileInfo:
    files: List[pathlib.Path]
    pg_migrations: List[pathlib.Path]

    def extend(self, other: ShardFiles) -> None:
        if other.files:
            self.files.extend(other.files)
        if other.pg_migrations:
            self.pg_migrations.extend(other.pg_migrations)


ShardPathesDict = Dict[int, ShardFileInfo]


@dataclasses.dataclass(frozen=True)
class PgShard:
    shard_id: int
    pretty_name: str
    dbname: str
    files: List[pathlib.Path]
    migrations: List[pathlib.Path]

    def get_schema_hash(self) -> str:
        return utils.get_files_hash(
            itertools.chain(self.files, self.migrations),
        )


@dataclasses.dataclass(frozen=True)
class PgShardedDatabase:
    service_name: str
    dbname: str
    shards: List[PgShard]


def find_schemas(
        service_name: Optional[str], schema_dirs: List[pathlib.Path],
) -> Dict[str, PgShardedDatabase]:
    """Read database schemas from directories ``schema_dirs``. ::
     |- schema_path/
       |- database1.sql
       |- database2.sql
    :param service_name: service name used as prefix for database name if not
           empty, e.g. "servicename_dbname".
    :param schema_dirs: list of pathes to scan for schemas
    :returns: :py:class:`Dict[str, PgShardedDatabase]` where key is
              database name as stored in :py:attr:`PgShard.dbname`
    """
    result: Dict[str, PgShardedDatabase] = {}
    for path in schema_dirs:
        if not path.is_dir():
            continue
        schemas = _find_databases_schemas(service_name, path)
        for dbname in schemas.keys() & result.keys():
            raise exceptions.PostgresqlError(
                f'Database {dbname} is declared twice',
            )
        result.update(schemas)
    return result


def _find_databases_schemas(
        service_name: Optional[str], schema_path: pathlib.Path,
) -> Dict[str, PgShardedDatabase]:
    logger.debug('Looking up for PostgreSQL schemas at %s', schema_path)
    shard_files_map = _build_shard_files_map(schema_path)
    result = {}
    for dbname, shards in shard_files_map.items():
        _raise_if_invalid_shards(dbname, shards)
        pg_shards = []
        for shard_id, shard_files in sorted(shards.items()):
            pg_shards.append(
                _create_pgshard(
                    dbname,
                    service_name=service_name,
                    shard_id=shard_id,
                    files=sorted(shard_files.files),
                    migrations=sorted(shard_files.pg_migrations),
                ),
            )
        result[dbname] = PgShardedDatabase(
            service_name=service_name, dbname=dbname, shards=pg_shards,
        )
    return result


def _build_shard_files_map(
        root_path: pathlib.Path,
) -> DefaultDict[str, ShardPathesDict]:
    result: DefaultDict[str, ShardPathesDict]
    result = collections.defaultdict(
        lambda: collections.defaultdict(lambda: ShardFileInfo([], [])),
    )
    for shard in _find_shard_files(root_path):
        result[shard.name.db_name][shard.name.shard].extend(shard)
    return result


def _find_shard_files(schema_path: pathlib.Path) -> Iterable[ShardFiles]:
    for entry in schema_path.iterdir():
        shard_files = _get_shard_schema_files(entry)
        if shard_files is not None:
            yield shard_files


def _get_shard_schema_files(path: pathlib.Path) -> Optional[ShardFiles]:
    shard_name = _parse_shard_name(path.stem)
    if path.is_file():
        if path.suffix == '.sql':
            return ShardFiles(shard_name, files=[path])
    elif path.is_dir():
        if path.joinpath('migrations').is_dir():
            return ShardFiles(shard_name, pg_migrations=[path])
        return ShardFiles(shard_name, files=utils.scan_sql_directory(path))
    return None


def _raise_if_invalid_shards(dbname: str, shards: ShardPathesDict) -> None:
    if SINGLE_SHARD in shards:
        if len(shards) != 1:
            raise exceptions.PostgresqlError(
                'Postgresql database %s has single shard configuration '
                'while defined as multishard' % (dbname,),
            )
    else:
        if set(shards.keys()) != set(range(len(shards))):
            raise exceptions.PostgresqlError(
                'Postgresql database %s is missing fixtures '
                'for some shards' % (dbname,),
            )


def _create_pgshard(
        dbname: str,
        service_name: Optional[str] = None,
        shard_id: int = SINGLE_SHARD,
        files: Optional[List[pathlib.Path]] = None,
        migrations: Optional[List[pathlib.Path]] = None,
) -> PgShard:
    if files is None:
        files = []
    if migrations is None:
        migrations = []
    if shard_id == SINGLE_SHARD:
        shard_id = 0
        pretty_name = dbname
        sharded_dbname = dbname
    else:
        shard_id = shard_id
        pretty_name = '%s@%d' % (dbname, shard_id)
        sharded_dbname = '%s_%d' % (dbname, shard_id)

    if service_name is not None:
        sharded_dbname = '%s_%s' % (
            _normalize_name(service_name),
            sharded_dbname,
        )
    return PgShard(
        shard_id=shard_id,
        pretty_name=pretty_name,
        dbname=sharded_dbname,
        files=files,
        migrations=migrations,
    )


def _parse_shard_name(name) -> ShardName:
    parts = name.rsplit('@', 1)
    if len(parts) == 2:
        try:
            shard_id = int(parts[1])
        except (ValueError, TypeError):
            pass
        else:
            return ShardName(parts[0], shard_id)
    return ShardName(name, SINGLE_SHARD)


def _normalize_name(name):
    return name.replace('.', '_').replace('-', '_')
