import contextlib
import multiprocessing.pool
import os
import pathlib
import pprint
import random
import re
import typing

import pymongo
import pymongo.collection
import pymongo.errors
import pytest

from testsuite import utils
from testsuite.environment import service

from . import ensure_db_indexes
from . import mongo_schema

# pylint: disable=too-many-statements

DB_FILE_RE_PATTERN = re.compile(r'/db_(?P<mongo_db_alias>\w+)\.json$')

DEFAULT_CONFIG_SERVER_PORT = 27118
DEFAULT_MONGOS_PORT = 27217
DEFAULT_SHARD_PORT = 27119

SERVICE_SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), 'scripts/service-mongo',
)


class BaseError(Exception):
    """Base testsuite error"""


class UnknownCollectionError(BaseError):
    pass


class CollectionWrapper:
    def __init__(self, collections):
        for alias, collection in collections.items():
            setattr(self, alias, collection)
        self._collections = collections.copy()
        self._aliases = tuple(collections.keys())

    def __getitem__(self, alias: str) -> pymongo.collection.Collection:
        return self._collections[alias]

    def __contains__(self, alias: str) -> bool:
        return alias in self._collections

    def get_aliases(self) -> typing.Tuple[str]:
        return self._aliases


class CollectionWrapperFactory:
    def __init__(self, mongo_host):
        self._mongo_host = mongo_host

    @property
    def connection_string(self):
        return self._mongo_host

    @utils.cached_property
    def client(self) -> pymongo.MongoClient:
        return pymongo.MongoClient(self._mongo_host)

    def create_collection_wrapper(
            self, collection_names, mongodb_settings,
    ) -> CollectionWrapper:
        collections = {}
        for name in collection_names:
            if name not in mongodb_settings:
                raise UnknownCollectionError(
                    f'Missing collection {name} in mongodb_settings fixture',
                )
            # pylint: disable=unsubscriptable-object
            settings = mongodb_settings[name]['settings']
            database = self.client[settings['database']]
            collections[name] = database[settings['collection']]
        return CollectionWrapper(collections)


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'noshuffledb: disable data set shuffle for marked test',
    )
    config.addinivalue_line(
        'markers', 'filldb: specify mongo static file suffix',
    )
    config.addinivalue_line(
        'markers', 'mongodb_collections: override mongo collections list',
    )


def pytest_addoption(parser):
    """
    :param parser: pytest's argument parser
    """
    group = parser.getgroup('mongo')
    group.addoption('--mongo', help='Mongo connection string.')
    group.addoption(
        '--no-indexes', action='store_true', help='Disable index creation.',
    )
    group.addoption(
        '--no-shuffle-db',
        action='store_true',
        help='Disable fixture data shuffle.',
    )
    group.addoption(
        '--no-sharding',
        action='store_true',
        help='Disable collections sharding.',
    )
    group.addoption(
        '--no-mongo', help='Disable mongo startup', action='store_true',
    )


def pytest_service_register(register_service):
    @register_service('mongo')
    def _create_mongo_service(
            service_name,
            working_dir,
            mongos_port=DEFAULT_MONGOS_PORT,
            config_server_port=DEFAULT_CONFIG_SERVER_PORT,
            shard_port=DEFAULT_SHARD_PORT,
            env=None,
    ):
        return service.ScriptService(
            service_name=service_name,
            script_path=SERVICE_SCRIPT_PATH,
            working_dir=working_dir,
            environment={
                'MONGO_TMPDIR': working_dir,
                'MONGOS_PORT': str(mongos_port),
                'CONFIG_SERVER_PORT': str(config_server_port),
                'SHARD_PORT': str(shard_port),
                **(env or {}),
            },
            check_ports=[config_server_port, mongos_port, shard_port],
        )


@pytest.fixture
def mongodb(mongodb_init, _mongodb_local) -> CollectionWrapper:
    return _mongodb_local


@pytest.fixture
def mongo_connections(
        mongodb_settings,
        mongo_host,
        mongo_extra_connections,
        _mongo_local_collections,
):
    return {
        **{
            mongodb_settings[name]['settings']['connection']: mongo_host
            for name in _mongo_local_collections
        },
        **{connection: mongo_host for connection in mongo_extra_connections},
    }


@pytest.fixture
def mongo_extra_connections():
    """
    Override this if you need to access mongo connections besides those
    defined in mongo_connections fixture
    """
    return ()


@pytest.fixture(scope='session')
def _mongo_indexes_ensured():
    return set()


@pytest.fixture
def _mongo_service(
        pytestconfig,
        ensure_service_started,
        _mongodb_local,
        _mongos_port,
        _mongo_config_server_port,
        _mongo_shard_port,
):
    aliases = _mongodb_local.get_aliases()
    if (
            aliases
            and not pytestconfig.option.mongo
            and not pytestconfig.option.no_mongo
    ):
        ensure_service_started(
            'mongo',
            mongos_port=_mongos_port,
            config_server_port=_mongo_config_server_port,
            shard_port=_mongo_shard_port,
        )


@pytest.fixture
def _mongo_create_indexes(
        _mongodb_local,
        mongodb_settings,
        pytestconfig,
        _mongo_indexes_ensured,
        _mongo_service,
):
    aliases = _mongodb_local.get_aliases()
    if not pytestconfig.option.no_indexes:
        _ensure_indexes = {}
        for alias in aliases:
            if (
                    alias not in _mongo_indexes_ensured
                    and alias in mongodb_settings
            ):
                _ensure_indexes[alias] = mongodb_settings[alias]
        if _ensure_indexes:
            sharding_enabled = not pytestconfig.option.no_sharding
            ensure_db_indexes.ensure_db_indexes(
                _mongodb_local,
                _ensure_indexes,
                sharding_enabled=sharding_enabled,
            )
            _mongo_indexes_ensured.update(_ensure_indexes)


@pytest.fixture(scope='session')
def _mongo_thread_pool():
    pool = multiprocessing.pool.ThreadPool(processes=20)
    with contextlib.closing(pool):
        yield pool


@pytest.fixture
def mongodb_init(
        request,
        _mongodb_local,
        load_json,
        now,
        _mongo_thread_pool,
        _mongo_create_indexes,
        verify_file_paths,
        static_dir,
):
    """Populate mongodb with fixture data."""

    if request.node.get_closest_marker('nofilldb'):
        return

    # Disable shuffle to make some buggy test work
    shuffle_enabled = (
        not request.config.option.no_shuffle_db
        and not request.node.get_closest_marker('noshuffledb')
    )
    aliases = {key: key for key in _mongodb_local.get_aliases()}
    requested = set()

    for marker in request.node.iter_markers('filldb'):
        for dbname, alias in marker.kwargs.items():
            if dbname not in aliases:
                raise UnknownCollectionError(
                    'Unknown collection %s requested' % (dbname,),
                )
            if alias != 'default':
                aliases[dbname] = '%s_%s' % (dbname, alias)
            requested.add(dbname)

    def _verify_db_alias(file_path: str):
        if not _is_relevant_file(request, static_dir, file_path):
            return True
        match = DB_FILE_RE_PATTERN.search(file_path)
        if match:
            db_alias = match.group('mongo_db_alias')
            if db_alias not in aliases and not any(
                    db_alias.startswith(alias + '_') for alias in aliases
            ):
                return False
        return True

    verify_file_paths(
        _verify_db_alias,
        check_name='mongo_db_aliases',
        text_at_fail='file has not valid mongo collection name alias '
        '(probably should add to service.yaml)',
    )

    def load_collection(params):
        dbname, alias = params
        try:
            col = getattr(_mongodb_local, dbname)
        except AttributeError:
            return
        try:
            docs = load_json('db_%s.json' % alias, now=now)
        except FileNotFoundError:
            if dbname in requested:
                raise
            docs = []
        if not docs and not col.count():
            return

        if shuffle_enabled:
            # Make sure there is no tests that depend on order of
            # documents in fixture file.
            random.shuffle(docs)

        try:
            col.bulk_write(
                [
                    pymongo.DeleteMany({}),
                    *(pymongo.InsertOne(doc) for doc in docs),
                ],
                ordered=True,
            )
        except pymongo.errors.BulkWriteError as bwe:
            pprint.pprint(bwe.details)
            raise

    pool_args = []
    for dbname, alias in aliases.items():
        pool_args.append((dbname, alias))

    _mongo_thread_pool.map(load_collection, pool_args)


@pytest.fixture
def _mongodb_local(
        mongodb_settings,
        _mongo_local_collections,
        _mongo_collection_wrapper_factory: CollectionWrapperFactory,
):
    return _mongo_collection_wrapper_factory.create_collection_wrapper(
        _mongo_local_collections, mongodb_settings,
    )


@pytest.fixture(scope='session')
def _mongo_collection_wrapper_factory(
        mongo_host: str,
) -> CollectionWrapperFactory:
    return CollectionWrapperFactory(mongo_host)


@pytest.fixture(scope='session')
def _mongos_port(worker_id, get_free_port) -> int:
    if worker_id == 'master':
        return DEFAULT_MONGOS_PORT
    return get_free_port()


@pytest.fixture(scope='session')
def _mongo_config_server_port(worker_id, get_free_port):
    if worker_id == 'master':
        return DEFAULT_CONFIG_SERVER_PORT
    return get_free_port()


@pytest.fixture(scope='session')
def _mongo_shard_port(worker_id, get_free_port):
    if worker_id == 'master':
        return DEFAULT_SHARD_PORT
    return get_free_port()


@pytest.fixture
def _mongo_local_collections(request, mongodb_collections):
    result = set(mongodb_collections)
    for marker in request.node.iter_markers('mongodb_collections'):
        result.update(marker.args)
    return result


@pytest.fixture
def mongodb_collections(mongodb_settings):
    """
    Override this to enable access to named collections within test module

    Returns all available collections by default.
    """
    return tuple(mongodb_settings.keys())


@pytest.fixture(scope='session')
def mongo_host(pytestconfig, _mongos_port):
    host = pytestconfig.option.mongo
    return host or _get_connection_string(_mongos_port)


@pytest.fixture
def mongodb_settings(
        mongo_schema_directory,
        mongo_schema_extra_directories,
        _mongo_schema_cache,
):
    return mongo_schema.MongoSchemas(
        _mongo_schema_cache,
        (mongo_schema_directory, *mongo_schema_extra_directories),
    )


@pytest.fixture(scope='session')
def mongo_schema_extra_directories():
    """
    Override to use collection schemas besides those defined by
    ``mongo_schema_directory`` fixture
    """
    return ()


@pytest.fixture(scope='session')
def _mongo_schema_cache():
    return mongo_schema.MongoSchemaCache()


def _is_relevant_file(request, static_dir, file_path):
    default_static_dir = os.path.join(static_dir, 'default')
    module_static_dir = os.path.join(
        static_dir, os.path.basename(request.fspath),
    )
    return _is_nested_path(file_path, default_static_dir) or _is_nested_path(
        file_path, module_static_dir,
    )


def _is_nested_path(parent: str, nested: str) -> bool:
    try:
        pathlib.PurePath(nested).relative_to(parent)
        return True
    except ValueError:
        return False


def _get_connection_string(port):
    return 'mongodb://localhost:%s/' % port
