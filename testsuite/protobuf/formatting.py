from google.protobuf import json_format as protobuf_format
from google.protobuf.message import Message


def proto_to_dict(proto: Message) -> dict:
    return protobuf_format.MessageToDict(
        proto,
        preserving_proto_field_name=True,
    )
