import json

import pytest


@pytest.mark.redis_store(['set', 'foo', 'bar'], ['hset', 'baz', 'quux', 'bat'])
@pytest.mark.nofilldb
def test_redis_marker_store(redis_store):
    assert redis_store.get('foo') == b'bar'
    assert redis_store.hgetall('baz') == {b'quux': b'bat'}


@pytest.mark.redis_store(file='use_redis_store_file')
@pytest.mark.nofilldb
def test_redis_store_file(redis_store):
    assert redis_store.get('foo') == b'store'
    _check_store_file(redis_store)


@pytest.mark.redis_store(['set', 'foo', 'bar'], file='use_redis_store_file')
@pytest.mark.nofilldb
# pylint: disable=invalid-name
def test_redis_store_file_with_overrides(redis_store):
    assert redis_store.get('foo') == b'bar'
    _check_store_file(redis_store)


@pytest.mark.redis_store(file='redis')
@pytest.mark.nofilldb
def test_redis_default(redis_store):
    assert redis_store.hgetall('baz') == {b'default': b'really default'}

    assert not redis_store.exists('foo')
    redis_store.hset('foo', 'qu', 'qux')
    assert redis_store.hgetall('foo') == {b'qu': b'qux'}


def _check_store_file(redis_store):
    assert redis_store.hgetall('baz') == {b'quux2': b'store'}

    assert redis_store.hkeys('complicated') == [b'key']
    assert json.loads(redis_store.hget('complicated', b'key')) == {
        'sub_key': 'subvalue',
    }
