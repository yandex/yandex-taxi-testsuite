import datetime

from bson import json_util

JSON_OPTIONS = json_util.JSONOptions(tz_aware=False)


def loads(string, *args, **kwargs):
    """Helper function that wraps ``json.loads``.

    Automatically passes the object_hook for BSON type conversion.
    """

    default_hook = kwargs.pop('object_hook', None)
    mockserver = kwargs.pop('mockserver', None)
    mockserver_https = kwargs.pop('mockserver_https', None)
    now = kwargs.pop('now', None)
    kwargs['object_hook'] = _build_object_hook(
        default_hook, mockserver, mockserver_https, now,
    )
    return json_util.json.loads(string, *args, **kwargs)


def substitute(
        json_obj,
        *,
        object_hook=None,
        mockserver=None,
        mockserver_https=None,
        now=None,
):
    """Create transformed json by making substitutions:

    {"$mockserver": "/path", "$schema": true} -> "http://localhost:9999/path"
    {"$dateDiff": 10} -> datetime.utcnow() + timedelta(seconds=10)
    """
    hook = _build_object_hook(object_hook, mockserver, mockserver_https, now)
    return _substitute(json_obj, hook)


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
        seconds = int(diff.total_seconds())
        return {'$dateDiff': seconds}
    return default(obj)


def _substitute(json_obj, hook):
    if isinstance(json_obj, dict):
        return hook(
            {key: _substitute(value, hook) for key, value in json_obj.items()},
        )
    if isinstance(json_obj, list):
        return hook([_substitute(element, hook) for element in json_obj])
    return json_obj


def _build_object_hook(default_hook, mockserver, mockserver_https, now=None):
    if now is None:
        now = datetime.datetime.utcnow()

    mockserver_substitutions = [
        ('$mockserver', mockserver),
        ('$mockserver_https', mockserver_https),
    ]

    def _hook(dct):
        for key, mockserver_info in mockserver_substitutions:
            if key in dct:
                if mockserver_info is None:
                    raise RuntimeError(f'Missing {key} argument')
                if not dct.get('$schema', True):
                    schema = ''
                elif mockserver_info.ssl is not None:
                    schema = 'https://'
                else:
                    schema = 'http://'
                return '%s%s:%d%s' % (
                    schema,
                    mockserver_info.host,
                    mockserver_info.port,
                    dct[key],
                )
        if '$dateDiff' in dct:
            seconds = int(dct['$dateDiff'])
            return now + datetime.timedelta(seconds=seconds)
        if default_hook is not None:
            return default_hook(dct)
        return json_util.object_hook(dct, JSON_OPTIONS)

    return _hook
