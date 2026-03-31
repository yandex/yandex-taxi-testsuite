import typing

import py.io

try:
    from google.protobuf import json_format as _protobuf_json_format
    from google.protobuf import message as _protobuf_message

    _PROTOBUF_AVAILABLE = True
except (ImportError, TypeError):
    _PROTOBUF_AVAILABLE = False


def proto_to_dict(msg: typing.Any) -> dict:
    if not _PROTOBUF_AVAILABLE:
        raise RuntimeError('google.protobuf is required for proto_to_dict')
    return _protobuf_json_format.MessageToDict(
        msg, preserving_proto_field_name=True
    )


def _protobuf_pair_predicate(left: typing.Any, right: typing.Any) -> bool:
    if not _PROTOBUF_AVAILABLE:
        return False
    return isinstance(left, _protobuf_message.Message)


def _protobuf_pair_visitor(
    transform,
    left: typing.Any,
    right: typing.Any,
) -> tuple:
    left_is_proto = isinstance(left, _protobuf_message.Message)
    right_is_proto = isinstance(right, _protobuf_message.Message)

    if not isinstance(right, (dict, _protobuf_message.Message)):
        transform.report_error(
            f'protobuf message or dict expected on the right, '
            f'got {py.io.saferepr(right)} instead',
        )
        return left, right

    if left_is_proto and right_is_proto and type(left) is not type(right):
        transform.report_error(
            f'protobuf type mismatch: '
            f'{type(left).__name__} != {type(right).__name__}',
        )
        return left, right

    left_dict = proto_to_dict(left) if left_is_proto else left
    right_dict = proto_to_dict(right) if right_is_proto else right
    return transform.visit_dict(left_dict, right_dict)


def _builtin_compare_visitor_pairs() -> list:
    if not _PROTOBUF_AVAILABLE:
        return []
    return [(_protobuf_pair_predicate, _protobuf_pair_visitor)]


def pytest_register_compare_visitors():
    return _builtin_compare_visitor_pairs()
