import collections.abc
import glob
import os
import typing

from testsuite.utils import yaml_util


class MongoSchema(collections.abc.Mapping):
    def __init__(self, directory):
        self._directory = directory
        self._loaded = {}
        self._paths = _get_paths(directory)

    def __getitem__(self, name):
        if name not in self._paths:
            raise KeyError(f'Missing schema file for collection {name}')
        if name not in self._loaded:
            self._loaded[name] = yaml_util.load_file(self._paths[name])
        return self._loaded[name]

    def __iter__(self):
        return iter(self._paths)

    def __len__(self) -> int:
        return len(self._paths)

    @property
    def directory(self):
        return self._directory


class MongoSchemaCache:
    def __init__(self):
        self._cache: typing.Dict[str, MongoSchema] = {}

    def get_schema(self, directory):
        if directory not in self._cache:
            self._cache[directory] = MongoSchema(directory)
        return self._cache[directory]


class MongoSchemas(collections.abc.Mapping):
    def __init__(
            self, cache: MongoSchemaCache, directories: typing.Iterable[str],
    ):
        self._cache = cache
        self._directories = directories
        self._schema_by_collection: typing.Dict[str, MongoSchema] = {}
        for directory in directories:
            schema = cache.get_schema(directory)
            for name in schema:
                if name in self._schema_by_collection:
                    raise RuntimeError(
                        f'Duplicate definition of collection {name}:\n'
                        f'  at {self._schema_by_collection[name].directory}\n'
                        f'  at {directory}',
                    )
                self._schema_by_collection[name] = schema

    def __getitem__(self, name):
        if name not in self._schema_by_collection:
            raise KeyError(f'Missing schema file for collection {name}')
        return self._schema_by_collection[name][name]

    def __iter__(self):
        for directory in self._directories:
            for name in self._cache.get_schema(directory):
                yield name

    def __len__(self) -> int:
        return sum(
            len(self._cache.get_schema(directory))
            for directory in self._directories
        )


def _get_paths(directory) -> typing.Dict[str, str]:
    result = {}
    for path in glob.glob(os.path.join(directory, '*.yaml')):
        collection, _ = os.path.splitext(os.path.basename(path))
        result[collection] = path
    return result
