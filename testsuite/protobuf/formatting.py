from google.protobuf import json_format
from google.protobuf.message import Message


def proto_to_dict(proto: Message) -> dict:
    return json_format.MessageToDict(
        proto,
        preserving_proto_field_name=True,
    )
