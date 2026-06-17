import google.protobuf.message

from testsuite.plugins.assertrepr_compare import CompareVisitor
from testsuite.protobuf.matching import ProtobufDictsImpl
from testsuite.protobuf.utils import message_to_dict


def _is_proto(value):
    return isinstance(value, google.protobuf.message.Message)


def _is_proto_dict(value):
    return isinstance(value, ProtobufDictsImpl)


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
        right = right._impl
        if isinstance(right, ProtobufDictsImpl):
            right = right._impl
    else:
        right = message_to_dict(right)
        if isinstance(left, ProtobufDictsImpl):
            left = left._impl

    return left, right


def pytest_register_compare_visitors() -> list[CompareVisitor]:
    return [
        CompareVisitor(predicate=_protobuf_predicate, visit=_protobuf_visitor),
        CompareVisitor(
            predicate=_proto_dicts_predicate, visit=_proto_dicts_visitor
        ),
    ]
