import pytest

pytest.importorskip('google.protobuf')

from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct

from testsuite._internal import compare_transform
from testsuite.plugins import assertrepr_protobuf


def _compare_visitors():
    pairs = assertrepr_protobuf.pytest_register_compare_visitors()
    if not pairs:
        pytest.skip('protobuf compare visitors require google.protobuf')
    return pairs


def _complex_nested_struct(*, leaf: float, row_value: float) -> Struct:
    struct = Struct()
    json_format.ParseDict(
        {
            'outer': {
                'middle': {
                    'inner': {'leaf': leaf},
                },
                'rows': [
                    {'name': 'a', 'value': 0.0},
                    {'name': 'b', 'value': row_value},
                ],
            },
        },
        struct,
    )
    return struct


def test_protobuf_nested_dict_mismatch_reports_deep_path():
    left = _complex_nested_struct(leaf=7.0, row_value=2.0)
    right = {
        'outer': {
            'middle': {
                'inner': {'leaf': 99.0},
            },
            'rows': [
                {'name': 'a', 'value': 0.0},
                {'name': 'b', 'value': 2.0},
            ],
        },
    }

    comparator = compare_transform.CompareTransform(
        compare_visitors=_compare_visitors(),
    )
    comparator.visit(left, right)
    assert comparator.errors
    leaf_path = "left['outer']['middle']['inner']['leaf']"
    assert leaf_path in comparator.errors
    assert any('!=' in msg for msg in comparator.errors[leaf_path])


def test_protobuf_nested_list_mismatch_reports_indexed_path():
    left = _complex_nested_struct(leaf=7.0, row_value=2.0)
    right = {
        'outer': {
            'middle': {
                'inner': {'leaf': 7.0},
            },
            'rows': [
                {'name': 'a', 'value': 0.0},
                {'name': 'b', 'value': 9.0},
            ],
        },
    }

    comparator = compare_transform.CompareTransform(
        compare_visitors=_compare_visitors(),
    )
    comparator.visit(left, right)
    assert comparator.errors
    row_path = "left['outer']['rows'][1]['value']"
    assert row_path in comparator.errors
    assert any('!=' in msg for msg in comparator.errors[row_path])


def test_protobuf_nested_proto_vs_proto_mismatch_reports_deep_path():
    left = _complex_nested_struct(leaf=1.0, row_value=0.0)
    right = _complex_nested_struct(leaf=2.0, row_value=0.0)

    comparator = compare_transform.CompareTransform(
        compare_visitors=_compare_visitors(),
    )
    comparator.visit(left, right)
    assert comparator.errors
    assert "left['outer']['middle']['inner']['leaf']" in comparator.errors
    assert any(
        '!=' in msg
        for msg in comparator.errors["left['outer']['middle']['inner']['leaf']"]
    )
