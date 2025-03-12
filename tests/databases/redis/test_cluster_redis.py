import json

import pytest


@pytest.mark.redis_cluster_store(
    ['set', 'foo', 'bar'], ['hset', 'baz', 'quux', 'bat']
)
@pytest.mark.nofilldb
def test_redis_marker_store(redis_cluster_store):
    assert redis_cluster_store.get('foo') == b'bar'
    assert redis_cluster_store.hgetall('baz') == {b'quux': b'bat'}


@pytest.mark.redis_cluster_store(file='use_redis_store_file')
@pytest.mark.nofilldb
def test_redis_store_file(redis_cluster_store, _check_store_file):
    assert redis_cluster_store.get('foo') == b'store'


@pytest.mark.redis_cluster_store(
    ['set', 'foo', 'bar'], file='use_redis_store_file'
)
@pytest.mark.nofilldb
# pylint: disable=invalid-name
def test_redis_store_file_with_overrides(
    redis_cluster_store, _check_store_file
):
    assert redis_cluster_store.get('foo') == b'bar'


@pytest.mark.redis_cluster_store(file='redis')
@pytest.mark.nofilldb
def test_redis_default(redis_cluster_store):
    assert redis_cluster_store.hgetall('baz') == {b'default': b'really default'}

    assert not redis_cluster_store.exists('foo')
    redis_cluster_store.hset('foo', 'qu', 'qux')
    assert redis_cluster_store.hgetall('foo') == {b'qu': b'qux'}


@pytest.fixture
def _check_store_file(redis_cluster_store):
    assert redis_cluster_store.hgetall('baz') == {b'quux2': b'store'}

    assert redis_cluster_store.hkeys('complicated') == [b'key']
    assert json.loads(redis_cluster_store.hget('complicated', b'key')) == {
        'sub_key': 'subvalue',
    }
