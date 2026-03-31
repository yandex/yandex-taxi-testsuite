import typing

import py.io
import pytest
from google.protobuf import message as protobuf_message

from testsuite.protobuf import formatting


def _protobuf_pair_predicate(left: typing.Any, right: typing.Any) -> bool:
    left_is_proto = isinstance(left, protobuf_message.Message)
    right_is_proto = isinstance(right, protobuf_message.Message)
    if not left_is_proto and not right_is_proto:
        return False
    return isinstance(left, (dict, protobuf_message.Message)) and isinstance(
        right,
        (dict, protobuf_message.Message),
    )


def _protobuf_pair_visitor(
    transform,
    left: typing.Any,
    right: typing.Any,
) -> tuple:
    left_is_proto = isinstance(left, protobuf_message.Message)
    right_is_proto = isinstance(right, protobuf_message.Message)

    if not isinstance(left, (dict, protobuf_message.Message)):
        transform.report_error(
            'protobuf Message or dict expected on the left, '
            f'got {py.io.saferepr(left)} instead',
        )
        return left, right
    if not isinstance(right, (dict, protobuf_message.Message)):
        transform.report_error(
            'protobuf Message or dict expected on the right, '
            f'got {py.io.saferepr(right)} instead',
        )
        return left, right

    if left_is_proto and right_is_proto and type(left) is not type(right):
        transform.report_error(
            'protobuf type mismatch: '
            f'{type(left).__name__} != {type(right).__name__}',
        )
        return left, right

    left_dict = formatting.proto_to_dict(left) if left_is_proto else left
    right_dict = formatting.proto_to_dict(right) if right_is_proto else right
    return transform.visit_dict(left_dict, right_dict)


def builtin_protobuf_compare_visitor_pairs() -> list:
    return [
        (_protobuf_pair_predicate, _protobuf_pair_visitor),
    ]


@pytest.hookimpl
def pytest_register_compare_visitors():
    return builtin_protobuf_compare_visitor_pairs()
