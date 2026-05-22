import google.protobuf.message

from testsuite.plugins.assertrepr_compare import CompareVisitor
from testsuite.protobuf.matching import PartialProtobufDict, ProtobufDict
from testsuite.protobuf.utils import message_to_dict


def _is_proto(value):
    return isinstance(value, google.protobuf.message.Message)


def _is_proto_dict(value):
    return isinstance(value, (ProtobufDict, PartialProtobufDict))


def _protobuf_predicate(left, right):
    return _is_proto(left) and _is_proto(right)


def _protobuf_visitor(left, right, reporter):
    return message_to_dict(left), message_to_dict(right)


def _proto_dicts_predicate(left, right):
    return (_is_proto(left) and _is_proto_dict(right)) or (
        _is_proto_dict(left) and _is_proto(right)
    )


def _proto_dicts_visitor(left, right, reporter):
    if _is_proto(left):
        left = message_to_dict(left)
        if isinstance(right, ProtobufDict):
            right = right._dict
        elif isinstance(right, PartialProtobufDict):
            right = right._partial
    else:
        right = message_to_dict(right)
        if isinstance(left, ProtobufDict):
            left = left._dict
        elif isinstance(left, PartialProtobufDict):
            left = left._partial

    return left, right


def pytest_register_compare_visitors() -> list[CompareVisitor]:
    return [
        CompareVisitor(predicate=_protobuf_predicate, visit=_protobuf_visitor),
        CompareVisitor(
            predicate=_proto_dicts_predicate, visit=_proto_dicts_visitor
        ),
    ]
