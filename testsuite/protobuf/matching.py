import google.protobuf.message

from testsuite.matching import PartialDict, recursive_partial_dict
from testsuite.protobuf.utils import message_to_dict


class ProtobufDict:
    """Strict protobuf matcher.

    Compares a protobuf message against an expected dict by converting the
    message via :py:func:`testsuite.protobuf.utils.message_to_dict` and
    requiring the resulting dict to equal the expected one exactly.

    Every field present in the message must appear in the expected dict
    (and vice versa). For partial matching where extra protobuf fields
    should be ignored, use :py:class:`PartialProtobufDict` or
    :py:func:`recursive_partial_protobuf` instead.

    Example:

    .. code-block:: python

       assert msg == matching.ProtobufDict({
           'first_name': 'John',
           'last_name': 'Doe',
           'status': 'STATUS_ACTIVE',
       })
    """

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
    """Partial protobuf matcher.

    Compares a protobuf message against an expected dict by converting the
    message via :py:func:`testsuite.protobuf.utils.message_to_dict` and
    delegating to :py:class:`testsuite.matching.PartialDict`. Only the
    keys listed in the expected dict are checked; any additional fields
    on the protobuf message are ignored.

    The match is only partial at the top level: nested dicts in the
    expected pattern still have to equal the corresponding nested
    message dicts exactly. Use :py:func:`recursive_partial_protobuf`
    when nested messages should also be matched partially.

    Example:

    .. code-block:: python

       # Passes regardless of other fields set on msg
       assert msg == matching.PartialProtobufDict({'first_name': 'John'})
    """

    def __init__(self, d):
        if isinstance(d, PartialDict):
            self._dict = dict(d)
            self._partial = d
        else:
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


def recursive_partial_protobuf(*args, **kwargs):
    """Recursive partial protobuf matcher.

    Same as :py:func:`testsuite.matching.recursive_partial_dict`, but the
    resulting matcher compares against a protobuf message after converting
    it to a dict via :py:func:`testsuite.protobuf.utils.message_to_dict`.

    Every nested dict in the expected pattern is wrapped in a
    :py:class:`testsuite.matching.PartialDict`, so unspecified fields of
    nested protobuf messages are ignored.

    Example:

    .. code-block:: python

       assert msg == matching.recursive_partial_protobuf({
           'first_name': 'John',
           'nested_field': {'inner_field': 1},
       })
    """
    return PartialProtobufDict(recursive_partial_dict(*args, **kwargs))
