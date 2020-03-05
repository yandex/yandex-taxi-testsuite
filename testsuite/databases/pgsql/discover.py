import collections
import logging
import pathlib
import typing

from . import exceptions
from . import utils

logger = logging.getLogger(__name__)

SINGLE_SHARD = -1


class ShardName(typing.NamedTuple):
    db_name: str
    shard: int


class ShardFiles(typing.NamedTuple):
    name: ShardName
    files: typing.List[str]


class PgShard:
    def __init__(
            self,
            dbname,
            service_name=None,
            shard_id: int = SINGLE_SHARD,
            files=(),
            migrations=None,
    ):
        if shard_id == SINGLE_SHARD:
            self.shard_id = 0
            self.pretty_name = dbname
            sharded_dbname = dbname
        else:
            self.shard_id = shard_id
            self.pretty_name = '%s@%d' % (dbname, shard_id)
            sharded_dbname = '%s_%d' % (dbname, shard_id)

        if service_name is not None:
            sharded_dbname = '%s_%s' % (
                _normalize_name(service_name),
                sharded_dbname,
            )
        self.dbname = sharded_dbname
        self.files = files
        self.migrations = migrations


class PgShardedDatabase:
    def __init__(self, service_name, dbname, shards):
        self.service_name = service_name
        self.dbname = dbname
        self.shards = shards

    def initialize(self, pgsql_control):
        logger.info(
            'Initializing database %s for service %s...',
            self.dbname,
            self.service_name,
        )
        connections = {}
        for shard in self.shards:
            logger.info('Creating database %s', shard.dbname)
            pgsql_control.create_database(shard.dbname)
            for path in shard.files:
                logger.info(
                    'Running sql script %s against database %s',
                    path,
                    shard.dbname,
                )
                schemas = pgsql_control.get_applied_schemas(shard.dbname)
                if path not in schemas:
                    pgsql_control.run_script(shard.dbname, path)
                    schemas.add(path)

            if shard.migrations:
                for path in shard.migrations:
                    logger.info(
                        'Running migrations from %s against database %s',
                        path,
                        shard.dbname,
                    )
                    schemas = pgsql_control.get_applied_schemas(shard.dbname)
                    if path not in schemas:
                        pgsql_control.run_migrations(shard.dbname, path)
                        schemas.add(path)

            connections[
                shard.pretty_name
            ] = pgsql_control.get_connection_cached(shard.dbname)
        return connections


def find_databases(
        service_name: str,
        schema_path: str,
        migrations_path: typing.Optional[str] = None,
        is_common_schema_path: bool = False,
) -> typing.Dict[str, PgShardedDatabase]:
    """Read database schemas from path ``schema_path``. ::

     |- schema_path/
       |- database1.sql
       |- database2.sql

    :param service_name: service name used as prefix for
        database name if not empty, e.g. "servicename_dbname".
    :param schema_path: path to schemas directory
    :param migrations_path: path to yandex-pgmigrate schemas
    :returns: dictionary ``{database_name: PgShardedDatabase}``
    """
    schemas: typing.Dict[str, PgShardedDatabase] = {}
    migrations: typing.Dict[str, PgShardedDatabase] = {}

    parsed_schema_path = pathlib.Path(schema_path)
    if parsed_schema_path.is_dir():
        schemas = _find_databases_schemas(
            service_name, parsed_schema_path, is_common_schema_path,
        )

    if migrations_path:
        parsed_migrations_path = pathlib.Path(migrations_path)
        if parsed_migrations_path.is_dir():
            migrations = _find_databases_migrations(
                service_name, parsed_migrations_path, is_common_schema_path,
            )

    for conflict in schemas.keys() & migrations.keys():
        raise exceptions.PostgresqlError(
            'Database %s has both migrations and schemas' % (conflict,),
        )

    return {**schemas, **migrations}


def _find_databases_schemas(
        service_name: str,
        schema_path: pathlib.Path,
        is_common_schema_path: bool,
) -> typing.Dict[str, PgShardedDatabase]:
    fixtures = _build_shard_files_map(
        schema_path, is_common_schema_path, _get_shard_schema_files,
    )
    result = {}
    for dbname, shards in fixtures.items():
        _raise_if_invalid_shards(dbname, shards)
        pg_shards = []
        for shard_id, shard_files in sorted(shards.items()):
            pg_shards.append(
                PgShard(
                    dbname,
                    service_name=service_name,
                    shard_id=shard_id,
                    files=sorted(shard_files),
                ),
            )
        result[dbname] = PgShardedDatabase(
            service_name=service_name, dbname=dbname, shards=pg_shards,
        )
    return result


def _find_databases_migrations(
        service_name,
        migrations_path: pathlib.Path,
        is_common_schemas_path: bool,
) -> typing.Dict[str, PgShardedDatabase]:
    migrations = _build_shard_files_map(
        migrations_path, is_common_schemas_path, _get_shard_migration_files,
    )
    result = {}
    for dbname, shards in migrations.items():
        _raise_if_invalid_shards(dbname, shards)
        pg_shards = []
        for shard_id, shard_directory in sorted(shards.items()):
            pg_shards.append(
                PgShard(
                    dbname,
                    service_name=service_name,
                    shard_id=shard_id,
                    migrations=shard_directory,
                ),
            )
        result[dbname] = PgShardedDatabase(
            service_name=service_name, dbname=dbname, shards=pg_shards,
        )
    return result


def _build_shard_files_map(
        root_path: pathlib.Path,
        is_common_schemas_path: bool,
        get_files: typing.Callable[
            [pathlib.Path], typing.Optional[ShardFiles],
        ],
) -> typing.DefaultDict[str, typing.DefaultDict[int, typing.List[str]]]:
    result: typing.DefaultDict[
        str, typing.DefaultDict[int, typing.List[str]],
    ] = collections.defaultdict(lambda: collections.defaultdict(list))
    shard_files: typing.Iterable[ShardFiles]
    if is_common_schemas_path:
        shard_files = _find_common_shard_files(root_path, get_files)
    else:
        shard_files = _find_shard_files(root_path, get_files)
    for shard in shard_files:
        result[shard.name.db_name][shard.name.shard].extend(shard.files)
    return result


def _find_shard_files(
        schema_path: pathlib.Path,
        get_files: typing.Callable[
            [pathlib.Path], typing.Optional[ShardFiles],
        ],
) -> typing.Iterable[ShardFiles]:
    for entry in schema_path.iterdir():
        shard_files = get_files(entry)
        if shard_files is not None:
            yield shard_files


def _find_common_shard_files(
        schema_path: pathlib.Path,
        get_files: typing.Callable[
            [pathlib.Path], typing.Optional[ShardFiles],
        ],
) -> typing.Iterable[ShardFiles]:
    for db_path in schema_path.iterdir():
        if db_path.is_file():
            raise exceptions.PostgresqlError(
                f'Unexpected file \'{db_path}\', in schemas directory. '
                f'Expected subdirectory \'{schema_path}/database_name\' '
                'for each database',
            )
        dbname = db_path.stem
        for entry_path in db_path.iterdir():
            shard_files = get_files(entry_path)
            if shard_files is None:
                continue
            if shard_files.name.db_name != dbname:
                raise exceptions.PostgresqlError(
                    f'Invalid dbname \'{shard_files.name.db_name}\', '
                    f'expected \'{dbname}\'',
                )
            yield shard_files


def _get_shard_schema_files(path: pathlib.Path) -> typing.Optional[ShardFiles]:
    name = path.stem
    ext = path.suffix
    shard_name = _parse_shard_name(name)
    if path.is_file():
        if ext == '.sql':
            return ShardFiles(shard_name, [str(path)])
    elif path.is_dir():
        files = [str(file) for file in utils.scan_sql_directory(str(path))]
        return ShardFiles(shard_name, files)
    return None


def _get_shard_migration_files(
        path: pathlib.Path,
) -> typing.Optional[ShardFiles]:
    if path.is_dir():
        shard_name = _parse_shard_name(path.stem)
        return ShardFiles(shard_name, [str(path)])
    return None


def _raise_if_invalid_shards(
        dbname: str, shards: typing.DefaultDict[int, typing.List[str]],
) -> None:
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
