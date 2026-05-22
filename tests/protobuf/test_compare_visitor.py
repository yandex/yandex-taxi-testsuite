import pytest

from tests.protobuf.proto.sample_message_pb2 import (  # type: ignore[attr-defined]
    SampleMessage,
    Status,
)
from testsuite.protobuf.pytest_plugin import message_to_dict


def test_message_to_dict_preserves_field_names():
    msg = SampleMessage(
        first_name='John',
        last_name='Doe',
        item_count=5,
        status=Status.STATUS_ACTIVE,
        display_name='Johnny',
        priority_level=3,
    )
    assert message_to_dict(msg) == {
        'first_name': 'John',
        'last_name': 'Doe',
        'item_count': 5,
        'status': 'STATUS_ACTIVE',
        'display_name': 'Johnny',
        'priority_level': 3,
    }


def test_message_to_dict_optional_fields():
    msg = SampleMessage(first_name='John', last_name='Doe')
    result = message_to_dict(msg)
    assert 'display_name' not in result
    assert 'priority_level' not in result


def test_equal_protobuf_messages_pass():
    left = SampleMessage(
        first_name='John',
        last_name='Doe',
        item_count=1,
        status=Status.STATUS_PENDING,
    )
    right = SampleMessage(
        first_name='John',
        last_name='Doe',
        item_count=1,
        status=Status.STATUS_PENDING,
    )
    assert left == right


def test_protobuf_compare_error_matches_dict_compare_error():
    left = SampleMessage(
        first_name='John',
        last_name='Doe',
        item_count=1,
        status=Status.STATUS_ACTIVE,
    )
    right = SampleMessage(
        first_name='Jane',
        last_name='Doe',
        item_count=1,
        status=Status.STATUS_INACTIVE,
    )

    with pytest.raises(AssertionError) as proto_exc:
        assert left == right

    with pytest.raises(AssertionError) as dict_exc:
        assert message_to_dict(left) == message_to_dict(right)

    assert str(proto_exc.value) == str(dict_exc.value)
