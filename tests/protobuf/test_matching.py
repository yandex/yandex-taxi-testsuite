import pytest

from tests.protobuf.proto.sample_message_pb2 import (  # type: ignore[attr-defined]
    Address,
    Contact,
    SampleMessage,
    Status,
)
from testsuite.matching import PartialDict, recursive_partial_dict
from testsuite.protobuf.matching import (
    PartialProtobufDict,
    ProtobufDict,
    RecursivePartialProtobufDict,
)


def make_msg(**kwargs):
    defaults = dict(
        first_name='John',
        last_name='Doe',
        item_count=1,
        status=Status.STATUS_ACTIVE,
    )
    defaults.update(kwargs)
    return SampleMessage(**defaults)


def make_nested_msg(**kwargs):
    defaults = dict(
        first_name='John',
        last_name='Doe',
        item_count=1,
        status=Status.STATUS_ACTIVE,
        contact=Contact(
            email='john@example.com',
            phone='+1234567890',
            address=Address(city='NYC', country='USA', zip_code='10001'),
        ),
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
    pattern = {
        'first_name': 'John',
        'last_name': 'Doe',
        'item_count': 1,
        'status': 'STATUS_ACTIVE',
    }
    expected = ProtobufDict(pattern)

    with pytest.raises(AssertionError) as proto_exc:
        assert msg == expected

    with pytest.raises(AssertionError) as dict_exc:
        assert {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_INACTIVE',
        } == pattern

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


def test_recursive_partial_protobuf_equal():
    msg = make_msg(display_name='Johnny', priority_level=5)
    assert msg == RecursivePartialProtobufDict({'first_name': 'John'})


def test_recursive_partial_protobuf_not_equal():
    msg = make_msg(first_name='Jane')
    assert msg != RecursivePartialProtobufDict({'first_name': 'John'})


def test_recursive_partial_protobuf_compare_error():
    msg = make_msg(first_name='Jane', status=Status.STATUS_INACTIVE)
    pattern = {'first_name': 'John', 'status': 'STATUS_ACTIVE'}
    recursive = RecursivePartialProtobufDict(pattern)

    with pytest.raises(AssertionError) as proto_exc:
        assert msg == recursive

    with pytest.raises(AssertionError) as dict_exc:
        assert {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_INACTIVE',
        } == recursive_partial_dict(pattern)

    assert str(proto_exc.value) == str(dict_exc.value)


def test_protobuf_dict_with_nested_partial_dict_equal():
    msg = make_nested_msg()
    assert msg == ProtobufDict(
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_ACTIVE',
            'contact': PartialDict({'email': 'john@example.com'}),
        }
    )


def test_protobuf_dict_with_nested_partial_dict_top_level_still_strict():
    msg = make_nested_msg()
    assert msg != ProtobufDict(
        {
            'first_name': 'John',
            'item_count': 1,
            'status': 'STATUS_ACTIVE',
            'contact': PartialDict({'email': 'john@example.com'}),
        }
    )


def test_protobuf_dict_with_nested_partial_dict_not_equal_on_nested_key():
    msg = make_nested_msg()
    assert msg != ProtobufDict(
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_ACTIVE',
            'contact': PartialDict({'email': 'someone-else@example.com'}),
        }
    )


def test_protobuf_dict_with_nested_recursive_partial_dict_equal():
    msg = make_nested_msg()
    assert msg == ProtobufDict(
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_ACTIVE',
            'contact': recursive_partial_dict({'address': {'city': 'NYC'}}),
        }
    )


def test_protobuf_dict_with_nested_recursive_partial_dict_not_equal_on_deep_key():
    msg = make_nested_msg()
    assert msg != ProtobufDict(
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_ACTIVE',
            'contact': recursive_partial_dict({'address': {'city': 'LA'}}),
        }
    )


def test_recursive_partial_protobuf_with_nested_partial_dict_equal():
    msg = make_nested_msg(first_name='Jane')
    assert msg == RecursivePartialProtobufDict(
        {
            'contact': PartialDict({'email': 'john@example.com'}),
        }
    )


def test_recursive_partial_protobuf_with_nested_partial_dict_opts_out_of_recursion():
    msg = make_nested_msg()
    assert msg != RecursivePartialProtobufDict(
        {
            'contact': PartialDict({'address': {'city': 'NYC'}}),
        }
    )


def test_recursive_partial_protobuf_with_nested_recursive_partial_dict_equal():
    msg = make_nested_msg()
    assert msg == RecursivePartialProtobufDict(
        {
            'contact': recursive_partial_dict({'address': {'city': 'NYC'}}),
        }
    )


def test_recursive_partial_protobuf_with_nested_recursive_partial_dict_equivalent_to_plain():
    msg = make_nested_msg()
    nested = RecursivePartialProtobufDict(
        {
            'contact': recursive_partial_dict({'address': {'city': 'NYC'}}),
        }
    )
    plain = RecursivePartialProtobufDict(
        {
            'contact': {'address': {'city': 'NYC'}},
        }
    )
    assert msg == nested
    assert msg == plain


def test_recursive_partial_protobuf_with_nested_recursive_partial_dict_not_equal_on_deep_key():
    msg = make_nested_msg()
    assert msg != RecursivePartialProtobufDict(
        {
            'contact': recursive_partial_dict({'address': {'city': 'LA'}}),
        }
    )


def test_recursive_partial_protobuf_nested_compare_error():
    msg = make_nested_msg()
    pattern = {'contact': {'address': {'city': 'LA'}}}
    recursive = RecursivePartialProtobufDict(pattern)

    with pytest.raises(AssertionError) as proto_exc:
        assert msg == recursive

    with pytest.raises(AssertionError) as dict_exc:
        assert {
            'first_name': 'John',
            'last_name': 'Doe',
            'item_count': 1,
            'status': 'STATUS_ACTIVE',
            'contact': {
                'email': 'john@example.com',
                'phone': '+1234567890',
                'address': {
                    'city': 'NYC',
                    'country': 'USA',
                    'zip_code': '10001',
                },
            },
        } == recursive_partial_dict(pattern)

    assert str(proto_exc.value) == str(dict_exc.value)
