import pytest


class ProtoEnvelope:
    __slots__ = ('message',)

    def __init__(self, message):
        self.message = message


def _envelope_predicate(left, right):
    return isinstance(left, ProtoEnvelope) and isinstance(right, ProtoEnvelope)


def _envelope_visitor(transform, left, right):
    return transform.visit(left.message, right.message)


@pytest.hookimpl
def pytest_register_compare_visitors():
    return [(_envelope_predicate, _envelope_visitor)]
