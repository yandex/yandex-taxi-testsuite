def create_db_collections(dbase, aliases):
    for alias in aliases:
        collection = getattr(dbase, alias, None)
        if collection is not None:
            _create_collection(collection)


def _create_collection(collection):
    collection.database.drop_collection(collection.name)
    collection.database.create_collection(collection.name)
