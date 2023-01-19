import pymongo

from . import utils


def create_collections(dbase, aliases):
    for alias in aliases:
        collection = getattr(dbase, alias, None)
        if collection is not None:
            collection.database.drop_collection(collection.name)
            collection.database.create_collection(collection.name)


def shard_collections(dbase, db_settings):
    for alias, value in db_settings.items():
        collection = getattr(dbase, alias, None)
        if collection is not None:
            sharding = value.get('sharding')
            if sharding:
                _shard_collection(collection, sharding)


def _shard_collection(collection, sharding):
    db_admin = collection.database.client.admin
    try:
        db_admin.command('enablesharding', collection.database.name)
    except pymongo.errors.OperationFailure as exc:
        if exc.code != 23:
            raise
    kwargs = _get_kwargs_for_shard_func(sharding)
    if not _is_collection_sharded(collection):
        db_admin.command('shardcollection', collection.full_name, **kwargs)



def _get_kwargs_for_shard_func(sharding):
    kwargs = {}

    for key, value in sharding.items():
        if key == 'key':
            if isinstance(value, str):
                sharding_key = {value: 1}
            elif isinstance(value, list):
                sharding_key = {}
                for obj in value:
                    sharding_key[obj['name']] = utils.SORT_STR_TO_PYMONGO[
                        obj['type']
                    ]
            else:
                raise ValueError('Cannot handle key: %r' % (value,))
            kwargs['key'] = sharding_key
        else:
            kwargs[key] = value

    return kwargs


def _is_collection_sharded(collection):
    collstats = collection.database.command('collstats', collection.name)
    return collstats.get('sharded')