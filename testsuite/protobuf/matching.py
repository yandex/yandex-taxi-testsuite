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


class PartialProtobufDict:
    """Partially compare a protobuf message against an expected dict."""

    def __init__(self, d: dict):
        self._dict = d
        self._partial = PartialDict(d)

    def __repr__(self):
        return f'<PartialProtobufDict {self._dict!r}>'

    def __eq__(self, other):
        if isinstance(other, google.protobuf.message.Message):
            return self._partial == message_to_dict(other)
        if isinstance(other, PartialProtobufDict):
            return self._partial == other._partial
        return False
