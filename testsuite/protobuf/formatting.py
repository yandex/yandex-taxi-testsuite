import typing

from google.protobuf import json_format as protobuf_format


def proto_to_dict(message: typing.Any) -> dict:
    return protobuf_format.MessageToDict(
        message,
        preserving_proto_field_name=True,
    )
