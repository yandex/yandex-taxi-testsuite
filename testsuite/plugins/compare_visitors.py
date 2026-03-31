import typing

import py.io

try:
    from google.protobuf import json_format as _protobuf_json_format
    from google.protobuf import message as _protobuf_message

    _PROTOBUF_AVAILABLE = True
except ImportError:
    _PROTOBUF_AVAILABLE = False


class Hookspec:
    def pytest_register_compare_visitors(self):
        pass


def _proto_to_dict(msg: '_protobuf_message.Message') -> dict:
    return _protobuf_json_format.MessageToDict(
        msg,
        preserving_proto_field_name=True,
        including_default_value_fields=True,
        float_precision=None,
    )


def proto_to_dict(msg: typing.Any) -> dict:
    if not _PROTOBUF_AVAILABLE:
        raise RuntimeError('google.protobuf is required for proto_to_dict')
    return _proto_to_dict(msg)


def _protobuf_pair_predicate(left: typing.Any, right: typing.Any) -> bool:
    if not _PROTOBUF_AVAILABLE:
        return False
    return isinstance(left, _protobuf_message.Message) and isinstance(
        right,
        (_protobuf_message.Message, dict),
    )


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

    left_dict = _proto_to_dict(left) if left_is_proto else left
    right_dict = _proto_to_dict(right) if right_is_proto else right
    return transform.visit_dict(left_dict, right_dict)


def _builtin_compare_visitor_pairs() -> list:
    if not _PROTOBUF_AVAILABLE:
        return []
    return [(_protobuf_pair_predicate, _protobuf_pair_visitor)]


class CompareVisitorsPlugin:
    def __init__(self):
        self._compare_visitors = []

    @property
    def compare_visitors(self):
        return self._compare_visitors

    def pytest_sessionstart(self, session):
        hook_results = (
            session.config.pluginmanager.hook.pytest_register_compare_visitors()
        )
        for items in hook_results:
            if items:
                self._compare_visitors.extend(items)
        self._compare_visitors.extend(_builtin_compare_visitor_pairs())

    def pytest_addhooks(self, pluginmanager):
        pluginmanager.add_hookspecs(Hookspec)


def pytest_configure(config):
    config.pluginmanager.register(
        CompareVisitorsPlugin(),
        'compare_visitors',
    )
