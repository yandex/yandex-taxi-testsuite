import typing

import google.protobuf.message

from testsuite.matching import PartialDict, recursive_partial_dict
from testsuite.protobuf.utils import message_to_dict


class ProtobufDictsImpl:
    def __init__(self, repr: dict, impl: typing.Any):
        self._repr = repr
        self._impl = impl

    def __repr__(self):
        return f'<type(self).__name__ {self._repr!r}>'

    def __eq__(self, other):
        if isinstance(other, google.protobuf.message.Message):
            return message_to_dict(other) == self._impl
        if type(self) == type(other):
            return self._impl == other._impl
        return False


class ProtobufDict(ProtobufDictsImpl):
    """Strict protobuf matcher.

    Compares a protobuf message against an expected dict by converting the
    message via :py:func:`testsuite.protobuf.utils.message_to_dict` and
    requiring the resulting dict to equal the expected one exactly.

    Every field present in the message must appear in the expected dict
    (and vice versa). For partial matching where extra protobuf fields
    should be ignored, use :py:class:`PartialProtobufDict` or
    :py:func:`RecursivePartialProtobufDict` instead.

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
        super().__init__(repr=d, impl=d)


class PartialProtobufDict(ProtobufDictsImpl):
    """Partial protobuf matcher.

    Compares a protobuf message against an expected dict by converting the
    message via :py:func:`testsuite.protobuf.utils.message_to_dict` and
    delegating to :py:class:`testsuite.matching.PartialDict`. Only the
    keys listed in the expected dict are checked; any additional fields
    on the protobuf message are ignored.

    The match is only partial at the top level: nested dicts in the
    expected pattern still have to equal the corresponding nested
    message dicts exactly. Use :py:class:`RecursivePartialProtobufDict`
    when nested messages should also be matched partially.

    Example:

    .. code-block:: python

       # Passes regardless of other fields set on msg
       assert msg == matching.PartialProtobufDict({'first_name': 'John'})
    """

    def __init__(self, d):
        super().__init__(repr=d, impl=PartialDict(d))


class RecursivePartialProtobufDict(ProtobufDictsImpl):
    """Recursive partial protobuf matcher.

    Same as :py:func:`testsuite.matching.recursive_partial_dict`, but the
    resulting matcher compares against a protobuf message after converting
    it to a dict via :py:func:`testsuite.protobuf.utils.message_to_dict`.


    Example:

    .. code-block:: python

       assert msg == matching.RecursivePartialProtobufDict({
           'first_name': 'John',
           'nested_field': {'inner_field': 1},
       })
    """

    def __init__(self, d):
        super().__init__(repr=d, impl=recursive_partial_dict(d))
