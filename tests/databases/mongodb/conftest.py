import pathlib

import pytest

pytest_plugins = [
    'testsuite.pytest_plugin',
    'testsuite.databases.mongo.pytest_plugin',
]


@pytest.fixture(scope='session')
def schemas_directory() -> pathlib.Path:
    return pathlib.Path(__file__).parent / 'schemas'


@pytest.fixture(scope='session')
def mongo_schema_directory(schemas_directory):
    return schemas_directory / 'mongo'
