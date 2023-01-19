import pymongo
import pytest

from . import utils


def ensure_db_indexes(dbase, db_settings):
    for alias, value in db_settings.items():
        collection = getattr(dbase, alias, None)
        if collection is not None:
            indexes = value.get('indexes')
            if indexes:
                for index in indexes:
                    _ensure_index(index, collection)
                index_info = collection.index_information()
                assert len(index_info) == len(indexes) + 1, (
                    'Collection {} have {} indexes, but must have {} '.format(
                        alias, len(index_info), len(indexes) + 1,
                    )
                )


def _ensure_index(index, collection):
    arg, kwargs = _get_args_for_ensure_func(index)
    kwargs.pop('expireAfterSeconds', None)
    try:
        collection.create_index(arg, **kwargs)
    except pymongo.errors.OperationFailure as exc:
        pytest.fail(
            'ensure_index() failed for %s: %s' % (collection.name, exc),
        )


def _get_args_for_ensure_func(index):
    kwargs = {}
    for key, value in index.items():
        if key == 'key':
            if isinstance(value, str):
                arg = index['key']
            elif isinstance(value, list):
                arg = []
                for obj in value:
                    arg.append((obj['name'], utils.SORT_STR_TO_PYMONGO[obj['type']]))
        else:
            kwargs[key] = value

    if 'background' not in kwargs:
        kwargs['background'] = True

    return arg, kwargs
