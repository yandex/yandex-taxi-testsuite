import pytest

from google.protobuf import json_format
from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp

from tests.protobuf.dynamic_sample import new_inner
from tests.protobuf.dynamic_sample import new_sample_message


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
    right = _complex_nested_struct(leaf=99.0, row_value=2.0)

    with pytest.raises(AssertionError) as excinfo:
        assert left == right
    text = str(excinfo.value)
    leaf_path = "left['outer']['middle']['inner']['leaf']"
    assert leaf_path in text
    assert '!=' in text


def test_protobuf_nested_list_mismatch_reports_indexed_path():
    left = _complex_nested_struct(leaf=7.0, row_value=2.0)
    right = _complex_nested_struct(leaf=7.0, row_value=9.0)

    with pytest.raises(AssertionError) as excinfo:
        assert left == right
    text = str(excinfo.value)
    row_path = "left['outer']['rows'][1]['value']"
    assert row_path in text
    assert '!=' in text


def _filled_sample(*, status: int, seconds: int, tags: tuple[str, ...]):
    msg = new_sample_message()
    msg.id = 'same-id'
    msg.status = status
    ts = Timestamp()
    ts.seconds = seconds
    ts.nanos = 500
    msg.created_at.CopyFrom(ts)
    inner = new_inner()
    inner.note = 'present'
    msg.inner.CopyFrom(inner)
    for tag in tags:
        msg.tags.append(tag)
    return msg


def test_protobuf_enum_mismatch_path():
    left = _filled_sample(status=1, seconds=10, tags=('x',))
    right = _filled_sample(status=2, seconds=10, tags=('x',))

    with pytest.raises(AssertionError) as excinfo:
        assert left == right
    text = str(excinfo.value)
    assert "left['status']" in text


def test_protobuf_timestamp_mismatch_path():
    left = _filled_sample(status=1, seconds=1, tags=())
    right = _filled_sample(status=1, seconds=2, tags=())

    with pytest.raises(AssertionError) as excinfo:
        assert left == right
    text = str(excinfo.value)
    assert "left['created_at']" in text
    assert '1970-01-01T00:00:01' in text
    assert '1970-01-01T00:00:02' in text


def test_protobuf_optional_inner_note_mismatch():
    left = _filled_sample(status=1, seconds=0, tags=())
    right = _filled_sample(status=1, seconds=0, tags=())
    right.inner.note = 'other'

    with pytest.raises(AssertionError) as excinfo:
        assert left == right
    text = str(excinfo.value)
    assert "left['inner']['note']" in text


def test_protobuf_optional_inner_presence_mismatch():
    left = new_sample_message()
    left.id = 'id'
    left.status = 1
    inner = new_inner()
    inner.note = 'only-left'
    left.inner.CopyFrom(inner)

    right = new_sample_message()
    right.id = 'id'
    right.status = 1

    with pytest.raises(AssertionError) as excinfo:
        assert left == right
    text = str(excinfo.value)
    assert 'inner' in text or 'len(left)' in text


def test_protobuf_repeated_tags_mismatch():
    left = _filled_sample(status=0, seconds=0, tags=('a', 'b'))
    right = _filled_sample(status=0, seconds=0, tags=('a', 'c'))

    with pytest.raises(AssertionError) as excinfo:
        assert left == right
    text = str(excinfo.value)
    assert "left['tags'][1]" in text
