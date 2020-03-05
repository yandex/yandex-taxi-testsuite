import pytest


@pytest.fixture(scope='session')
def mongodb_collections():
    return ['foo']


def test_db_simple(mongodb):
    assert mongodb.foo.find_one('unknown') is None
    assert mongodb.foo.find_one('one') == {
        '_id': 'one',
        'source': 'db_foo.json',
    }


@pytest.mark.filldb(foo='own_fixture')
def test_db_own_fixture(mongodb):
    assert mongodb.foo.find_one('unknown') is None
    assert mongodb.foo.find_one('one') == {
        '_id': 'one',
        'source': 'db_foo_own_fixture.json',
    }
