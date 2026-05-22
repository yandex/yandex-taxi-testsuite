import google.protobuf.json_format
import google.protobuf.message


def message_to_dict(msg) -> dict:
    """Convert a protobuf message to a plain dict, preserving field names."""
    return google.protobuf.json_format.MessageToDict(
        msg,
        preserving_proto_field_name=True,
    )
