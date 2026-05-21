import pytest

from tests.protobuf.proto.sample_message_pb2 import SampleMessage, Status
from testsuite.matching import PartialDict
from testsuite.protobuf.matching import PartialProtobufDict, ProtobufDict


def make_msg(**kwargs):
    defaults = dict(
        first_name='John',
        last_name='Doe',
        item_count=1,
        status=Status.STATUS_ACTIVE,
    )
    defaults.update(kwargs)
    return SampleMessage(**defaults)


def test_protobuf_dict_equal():
    msg = make_msg()
    assert msg == ProtobufDict(
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_ACTIVE',
        }
    )


def test_protobuf_dict_not_equal():
    msg = make_msg(first_name='Jane')
    assert msg != ProtobufDict(
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_ACTIVE',
        }
    )


def test_protobuf_dict_compare_error():
    msg = make_msg(first_name='Jane', status=Status.STATUS_INACTIVE)
    expected = ProtobufDict(
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_ACTIVE',
        }
    )

    with pytest.raises(AssertionError) as proto_exc:
        assert msg == expected

    with pytest.raises(AssertionError) as dict_exc:
        assert {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_INACTIVE',
        } == expected._dict

    assert str(proto_exc.value) == str(dict_exc.value)


def test_partial_protobuf_dict_equal():
    msg = make_msg(display_name='Johnny', priority_level=5)
    assert msg == PartialProtobufDict({'first_name': 'John'})


def test_partial_protobuf_dict_not_equal():
    msg = make_msg(first_name='Jane')
    assert msg != PartialProtobufDict({'first_name': 'John'})


def test_partial_protobuf_dict():
    assert PartialProtobufDict({'first_name': 'John'}) == PartialProtobufDict(
        {'first_name': 'John'}
    )

    assert PartialProtobufDict({'first_name': 'John'}) != PartialProtobufDict(
        {'first_name': 'Jane'}
    )

    assert PartialProtobufDict({'first_name': 'John'}) != {'first_name': 'John'}
    assert PartialProtobufDict({'first_name': 'John'}) != 'John'
    assert PartialProtobufDict({'first_name': 'John'}) != 42


def test_partial_protobuf_dict_compare_error():
    msg = make_msg(first_name='Jane', status=Status.STATUS_INACTIVE)
    partial = PartialProtobufDict(
        {'first_name': 'John', 'status': 'STATUS_ACTIVE'}
    )

    with pytest.raises(AssertionError) as proto_exc:
        assert msg == partial

    with pytest.raises(AssertionError) as dict_exc:
        assert {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_INACTIVE',
        } == PartialDict({'first_name': 'John', 'status': 'STATUS_ACTIVE'})

    assert str(proto_exc.value) == str(dict_exc.value)
