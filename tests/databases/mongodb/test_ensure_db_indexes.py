import pymongo
import pytest

from testsuite.databases.mongo import ensure_db_indexes


@pytest.fixture(scope='session')
def mongodb_collections():
    return ['sharded_collection']


@pytest.mark.parametrize(
    'index_from_yaml, arg_and_kwargs',
    [
        ({'key': 'field'}, ('field', {'background': True})),
        (
            {'key': 'field', 'background': False},
            ('field', {'background': False}),
        ),
        (
            {
                'key': 'field',
                'expireAfterSeconds': 2592000,
                'sparse': True,
                'unique': True,
                'name': 'name',
            },
            (
                'field',
                {
                    'expireAfterSeconds': 2592000,
                    'sparse': True,
                    'unique': True,
                    'name': 'name',
                    'background': True,
                },
            ),
        ),
        (
            {
                'key': [
                    {'name': 'field', 'type': 'ascending'},
                    {'name': 'field_2', 'type': 'descending'},
                    {'name': 'field_3', 'type': '2d'},
                    {'name': 'field_4', 'type': '2dsphere'},
                    {'name': 'field_5', 'type': 'hashed'},
                    {'name': 'field_6', 'type': 'ascending'},
                    {'name': 'field_7', 'type': 'text'},
                ],
            },
            (
                [
                    ('field', pymongo.ASCENDING),
                    ('field_2', pymongo.DESCENDING),
                    ('field_3', pymongo.GEO2D),
                    ('field_4', pymongo.GEOSPHERE),
                    ('field_5', pymongo.HASHED),
                    ('field_6', pymongo.ASCENDING),
                    ('field_7', pymongo.TEXT),
                ],
                {'background': True},
            ),
        ),
        (
            {
                'key': 'field',
                'partialFilterExpression': {
                    'is_added_to_balance': {'$eq': 'holded'},
                },
            },
            (
                'field',
                {
                    'partialFilterExpression': {
                        'is_added_to_balance': {'$eq': 'holded'},
                    },
                    'background': True,
                },
            ),
        ),
    ],
)
def test_arg_and_kwargs_generation(index_from_yaml, arg_and_kwargs):
    # pylint: disable=protected-access
    assert (
        ensure_db_indexes._get_args_for_ensure_func(index_from_yaml)
        == arg_and_kwargs
    )


def test_sharded_collection(mongodb, pytestconfig):
    if not pytestconfig.option.no_sharding:
        return

    mongodb.sharded_collection.insert({'_id': 'foo', '_shard_id': 0})
    with pytest.raises(pymongo.errors.WriteError):
        mongodb.sharded_collection.insert({'_id': 'bar'})
