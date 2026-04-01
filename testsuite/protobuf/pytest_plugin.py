import typing

import py.io
import pytest
from google.protobuf import message as protobuf_message

from testsuite.protobuf import formatting


def _protobuf_pair_predicate(left: typing.Any, right: typing.Any) -> bool:
    left_is_proto = isinstance(left, protobuf_message.Message)
    right_is_proto = isinstance(right, protobuf_message.Message)
    if not left_is_proto or not right_is_proto:
        return False
    return True


def _protobuf_pair_visitor(
    transform,
    left: typing.Any,
    right: typing.Any,
) -> tuple:
    if type(left) is not type(right):
        transform.report_error(
            'protobuf type mismatch: '
            f'{type(left).__name__} != {type(right).__name__}',
        )
        return left, right

    left_dict = formatting.proto_to_dict(left)
    right_dict = formatting.proto_to_dict(right)
    return transform.visit_dict(left_dict, right_dict)


def builtin_protobuf_compare_visitor_pairs() -> list:
    return [
        (_protobuf_pair_predicate, _protobuf_pair_visitor),
    ]


@pytest.hookimpl
def pytest_register_compare_visitors():
    return builtin_protobuf_compare_visitor_pairs()
