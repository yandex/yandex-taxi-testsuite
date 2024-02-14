import datetime

from .cached_property import cached_property


def to_utc(stamp: datetime.datetime) -> datetime.datetime:
    if stamp.tzinfo is not None:
        stamp = stamp.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return stamp


def timestring(stamp: datetime.datetime) -> str:
    stamp = to_utc(stamp)
    return stamp.strftime('%Y-%m-%dT%H:%M:%S.%f+0000')


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def utcfromtimestamp(stamp: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(
        stamp, tz=datetime.timezone.utc
    ).replace(tzinfo=None)
