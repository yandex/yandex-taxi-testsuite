import os

import pytest


@pytest.fixture(scope='session')
def mongo_schema_extra_directories():
    extra_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.path.pardir,
            os.path.pardir,
            'schemas',
            'mongo_extra',
        ),
    )
    return (extra_dir,)


def test_extra_collection_is_accessible(mongodb):
    assert 'foo_extra' in mongodb.get_aliases()


def test_regular_collection_is_accessible(mongodb):
    assert 'foo' in mongodb.get_aliases()
