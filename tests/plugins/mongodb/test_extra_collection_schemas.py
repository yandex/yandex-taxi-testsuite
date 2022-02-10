import pathlib

import pytest


@pytest.fixture(scope='session')
def mongo_schema_extra_directories():
    return [
        pathlib.Path(__file__).parent.parent.parent / 'schemas/mongo_extra',
    ]


def test_extra_collection_is_accessible(mongodb):
    assert 'foo_extra' in mongodb.get_aliases()


def test_regular_collection_is_accessible(mongodb):
    assert 'foo' in mongodb.get_aliases()
