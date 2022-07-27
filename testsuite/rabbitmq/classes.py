import dataclasses

from pika.adapters.blocking_connection import (
    BlockingChannel,
    BlockingConnection,
)
from pika import ConnectionParameters
from pika.exchange_type import ExchangeType


@dataclasses.dataclass(frozen=True)
class ConnectionInfo:
    """RabbitMQ connection parameters"""

    host: str
    tcp_port: int


class Channel:
    def __init__(self, channel: BlockingChannel):
        self._channel = channel
        self._channel.confirm_delivery()

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self._channel.close()

    def declare_exchange(
        self, exchange: str, exchange_type: ExchangeType
    ) -> None:
        self._channel.exchange_declare(
            exchange=exchange, exchange_type=exchange_type
        )

    def declare_queue(self, queue: str) -> None:
        self._channel.queue_declare(queue=queue)

    def bind_queue(self, exchange: str, queue: str, routing_key: str) -> None:
        self._channel.queue_bind(
            queue=queue, exchange=exchange, routing_key=routing_key
        )

    def publish(self, exchange: str, routing_key: str, body: bytes):
        self._channel.basic_publish(
            exchange=exchange, routing_key=routing_key, body=body
        )

    def consume(self, queue: str, count: int, timeout: float = 2.0):
        result = []
        try:
            for _, _, body in self._channel.consume(
                queue=queue, inactivity_timeout=timeout
            ):
                result.append(body)
                if len(result) == count:
                    break
        finally:
            self._channel.cancel()

        return result


class Client:
    def __init__(self, connection: BlockingConnection):
        self._connection = connection

    def get_channel(self) -> Channel:
        return Channel(channel=self._connection.channel())


class Control:
    def __init__(self, enabled: bool, conn_info: ConnectionInfo):
        self._enabled = enabled
        if self._enabled:
            parameters = ConnectionParameters(
                host=conn_info.host, port=conn_info.tcp_port
            )
            self._client = Client(
                connection=BlockingConnection(parameters=parameters)
            )

    def get_channel(self) -> Channel:
        if not self._enabled:
            raise Exception("rabbitmq is disabled")

        return self._client.get_channel()
