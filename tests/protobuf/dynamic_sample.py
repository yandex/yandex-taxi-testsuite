import google.protobuf.timestamp_pb2  # noqa: F401

from google.protobuf import descriptor_pb2
from google.protobuf import descriptor_pool
from google.protobuf.message_factory import GetMessageClass

_pool = descriptor_pool.Default()
_registered = False


def _file_descriptor_proto() -> descriptor_pb2.FileDescriptorProto:
    fp = descriptor_pb2.FileDescriptorProto()
    fp.name = 'ts/assertrepr/sample.proto'
    fp.package = 'ts.assertrepr'
    fp.syntax = 'proto3'
    fp.dependency.append('google/protobuf/timestamp.proto')

    enum = fp.enum_type.add()
    enum.name = 'Status'
    for name, number in (
        ('STATUS_UNKNOWN', 0),
        ('STATUS_OK', 1),
        ('STATUS_FAIL', 2),
    ):
        val = enum.value.add()
        val.name = name
        val.number = number

    inner = fp.message_type.add()
    inner.name = 'Inner'
    f = inner.field.add()
    f.name = 'note'
    f.number = 1
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    msg = fp.message_type.add()
    msg.name = 'SampleMessage'

    f = msg.field.add()
    f.name = 'id'
    f.number = 1
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    f = msg.field.add()
    f.name = 'status'
    f.number = 2
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_ENUM
    f.type_name = '.ts.assertrepr.Status'

    f = msg.field.add()
    f.name = 'created_at'
    f.number = 3
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    f.type_name = '.google.protobuf.Timestamp'

    f = msg.field.add()
    f.name = 'inner'
    f.number = 4
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    f.type_name = '.ts.assertrepr.Inner'

    f = msg.field.add()
    f.name = 'tags'
    f.number = 5
    f.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
    f.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    return fp


def _ensure_registered() -> None:
    global _registered
    if _registered:
        return
    _pool.Add(_file_descriptor_proto())
    _registered = True


def new_sample_message():
    _ensure_registered()
    desc = _pool.FindMessageTypeByName('ts.assertrepr.SampleMessage')
    return GetMessageClass(desc)()


def new_inner():
    _ensure_registered()
    desc = _pool.FindMessageTypeByName('ts.assertrepr.Inner')
    return GetMessageClass(desc)()
