# flake8: noqa
import pytz

from .cached_property import cached_property


def to_utc(stamp):
    if stamp.tzinfo is not None:
        stamp = stamp.astimezone(pytz.utc).replace(tzinfo=None)
    return stamp


def timestring(stamp):
    stamp = to_utc(stamp)
    return stamp.strftime('%Y-%m-%dT%H:%M:%S.%f+0000')
