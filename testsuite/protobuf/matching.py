import collections.abc

import google.protobuf.message

from testsuite.matching import PartialDict
from testsuite.protobuf.utils import message_to_dict


class ProtobufDict:
    """Compare a protobuf message against an expected dict."""

    __testsuite_types__ = (google.protobuf.message.Message,)

    def __init__(self, d: dict):
        self._dict = d

    def __repr__(self):
        return f'<ProtobufDict {self._dict!r}>'

    def __eq__(self, other):
        if isinstance(other, google.protobuf.message.Message):
            return message_to_dict(other) == self._dict
        if isinstance(other, ProtobufDict):
            return self._dict == other._dict
        return False


class PartialProtobufDict(PartialDict):
    """Partially compare a protobuf message against an expected dict."""

    def __repr__(self):
        return f'<PartialProtobufDict {self._dict!r}>'

    def __eq__(self, other):
        if isinstance(other, google.protobuf.message.Message):
            return super().__eq__(message_to_dict(other))
        return super().__eq__(other)
