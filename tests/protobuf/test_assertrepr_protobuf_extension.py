import pytest
from google.protobuf.timestamp_pb2 import Timestamp

from tests.protobuf.dynamic_sample import new_inner, new_sample_message
from tests.protobuf.envelope_plugin import ProtoEnvelope


def _sample_with_ts(seconds: int):
    msg = new_sample_message()
    msg.id = 'x'
    msg.status = 1
    ts = Timestamp()
    ts.seconds = seconds
    msg.created_at.CopyFrom(ts)
    inner = new_inner()
    inner.note = 'n'
    msg.inner.CopyFrom(inner)
    return msg


def test_custom_envelope_visitor_compares_wrapped_protobuf():
    left = ProtoEnvelope(_sample_with_ts(1))
    right = ProtoEnvelope(_sample_with_ts(9))

    with pytest.raises(AssertionError) as excinfo:
        assert left == right
    text = str(excinfo.value)
    assert "left['created_at']" in text
    assert '1970-01-01T00:00:01' in text
    assert '1970-01-01T00:00:09' in text
