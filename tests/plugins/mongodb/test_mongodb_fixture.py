import pytest


@pytest.fixture(scope='session')
def mongodb_collections():
    return ['foo']


def test_mongodb_fixture(mongodb):
    assert mongodb.get_aliases() == ('foo',)


def test_fixtures_loaded(mongodb):
    assert mongodb.foo.find_one() == {'_id': 'foo'}


@pytest.mark.mongodb_collections('bar')
def test_mark_adds_collection_to_mongodb(mongodb):
    assert set(mongodb.get_aliases()) == {'foo', 'bar'}
