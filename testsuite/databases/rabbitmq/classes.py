import dataclasses
import typing


@dataclasses.dataclass(frozen=True)
class ConnectionInfo:
    """RabbitMQ connection parameters"""

    host: str
    tcp_port: int
    # vhost?
