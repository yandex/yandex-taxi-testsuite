import pytest

pytest.importorskip('google.protobuf')

from google.protobuf.timestamp_pb2 import Timestamp

from tests.core.plugins.protobuf.dynamic_sample import new_inner
from tests.core.plugins.protobuf.dynamic_sample import new_sample_message
from tests.core.plugins.protobuf.envelope_plugin import ProtoEnvelope


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
    assert "left['created_at']['seconds']" in text
