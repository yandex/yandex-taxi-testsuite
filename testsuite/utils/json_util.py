import datetime

from bson import json_util

from testsuite.utils import object_hook as object_hook_util


def loads(string, *args, **kwargs):
    """Helper function that wraps ``json.loads``.

    Automatically passes the object_hook for BSON type conversion.
    """

    object_hook = kwargs.pop('object_hook', None)
    kwargs['object_hook'] = object_hook_util.build_object_hook(
        object_hook=object_hook,
    )
    return json_util.json.loads(string, *args, **kwargs)


def substitute(json_obj, *, object_hook=None):
    """Create transformed json by making substitutions:

    {"$mockserver": "/path", "$schema": true} -> "http://localhost:9999/path"
    {"$dateDiff": 10} -> datetime.utcnow() + timedelta(seconds=10)
    """
    hook = object_hook_util.build_object_hook(object_hook=object_hook)
    return object_hook_util.substitute(json_obj, hook)


def dumps(obj, *args, **kwargs):
    """Helper function that wraps ``json.dumps``.

    This function does NOT support ``bson.binary.Binary`` and
    ``bson.code.Code`` types. It just passes ``default`` argument to
    ``json.dumps`` function.
    """
    kwargs['ensure_ascii'] = kwargs.get('ensure_ascii', False)
    kwargs['sort_keys'] = kwargs.get('sort_keys', True)
    kwargs['indent'] = kwargs.get('indent', 2)
    kwargs['separators'] = kwargs.get('separators', (',', ': '))

    if 'default' not in kwargs:
        if kwargs.pop('relative_datetimes', False):
            kwargs['default'] = relative_dates_default
        else:
            kwargs['default'] = default
    return json_util.json.dumps(obj, *args, **kwargs)


def default(obj):
    obj = json_util.default(obj)
    if isinstance(obj, datetime.datetime):
        return obj.replace(tzinifo=None)
    return obj


def relative_dates_default(obj):
    """Add ``$dateDiff`` hook to ``bson.json_util.default``."""
    if isinstance(obj, datetime.datetime):
        diff = obj.replace(tzinfo=None) - datetime.datetime.utcnow()
        return {'$dateDiff': diff.total_seconds()}
    return default(obj)
