import asyncio
import typing
import aiokafka
import logging


class KafkaDisabledError(Exception):
    pass


class KafkaProducer:
    """
    Kafka producer wrapper.
    The producer instance are created for each test.
    """

    def __init__(self, enabled: bool, server_port: int):
        self._enabled = enabled
        self._server_port = server_port

    async def start(self):
        if self._enabled:
            self.producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=f'localhost:{self._server_port}',
            )
            await self.producer.start()

    async def send(
        self,
        topic: str,
        key: str,
        value: str,
        partition: typing.Optional[int] = None,
    ):
        """
        Sends the message (``value``) to ``topic`` by ``key`` and,
        optionally, to a given ``partition`` and waits until it is delivered.
        If the call is successfully awaited,
        message is guaranteed to be delivered.

        :param topic: topic name.
        :param key: key. Needed to determine message's partition.
        :param value: message payload. Must be valid UTF-8.
        :param partition: Optional message partition.
            If not passed, determined by internal partitioner
            depends on key's hash.
        """

        resp_future = await self.send_async(topic, key, value, partition)
        await resp_future

    async def send_async(
        self,
        topic: str,
        key: str,
        value: str,
        partition: typing.Optional[int] = None,
    ):
        """
        Sends the message (``value``) to ``topic`` by ``key`` and,
        optionally, to a given ``partition`` and
        returns the future for message delivery awaiting.

        :param topic: topic name.
        :param key: key. Needed to determine message's partition.
        :param value: message payload. Must be valid UTF-8.
        :param partition: Optional message partition.
            If not passed, determined by internal partitioner
            depends on key's hash.
        """

        if not self._enabled:
            raise KafkaDisabledError

        return await self.producer.send(
            topic=topic,
            value=value.encode(),
            key=key.encode(),
            partition=partition,
        )

    async def teardown(self):
        if self._enabled:
            await self.producer.stop()


class ConsumedMessage:
    """Wrapper for consumed record."""

    topic: str
    key: str
    value: str
    partition: int
    offset: int

    def __init__(self, record: aiokafka.ConsumerRecord):
        self.topic = record.topic
        self.key = record.key.decode()
        self.value = record.value.decode()
        self.partition = record.partition
        self.offset = record.offset


class KafkaConsumer:
    """
    Kafka balanced consumer wrapper.
    The consumer instance are created for each test.
    All consumers are created with the same group.id,
    after each test consumer commits offsets for all consumed messages.
    This is needed to make tests independent.
    """

    def __init__(self, enabled: bool, server_port: int):
        self._enabled = enabled
        self._server_port = server_port
        self._subscribed_topics: typing.List[str] = list()

    async def start(self):
        if self._enabled:
            self.consumer = aiokafka.AIOKafkaConsumer(
                group_id='Test-group',
                bootstrap_servers=f'localhost:{self._server_port}',
                auto_offset_reset='earliest',
                enable_auto_commit=False,
            )
            await self.consumer.start()

    def _subscribe(self, topics: typing.List[str]):
        if not self._enabled:
            raise KafkaDisabledError

        to_subscribe: typing.List[str] = []
        for topic in topics:
            if topic not in self._subscribed_topics:
                to_subscribe.append(topic)

        if to_subscribe:
            logging.warning(f"Subscribing to {to_subscribe}")
            self.consumer.subscribe(to_subscribe)
            self._subscribed_topics.extend(to_subscribe)

    async def _commit(self):
        if not self._enabled:
            raise KafkaDisabledError

        self.consumer.commit()

    async def receive_one(
        self, topics: typing.List[str], timeout: float = 20.0
    ) -> ConsumedMessage:
        """
        Waits until one message are consumed.

        :param topics: list of topics to read messages from.
        :param timeout: timeout to stop waiting. Default is 20 seconds.

        :returns: :py:class:`ConsumedMessage`
        """
        if not self._enabled:
            raise KafkaDisabledError

        self._subscribe(topics)

        async def _do_receive():
            record: aiokafka.ConsumerRecord = await self.consumer.getone()
            return ConsumedMessage(record)

        logging.warning('Waiting for response')
        return await asyncio.wait_for(_do_receive(), timeout=timeout)

    async def receive_batch(
        self,
        topics: typing.List[str],
        max_batch_size: typing.Optional[int],
        timeout_ms: int = 3000,
    ) -> typing.List[ConsumedMessage]:
        """
        Waits until either ``max_batch_size`` messages are consumed or
        ``timeout_ms`` timeout expired.

        :param topics: list of topics to read messages from.
        :max_batch_size: maximum number of consumed messages.
        :param timeout_ms: timeout to stop waiting. Default is 3 seconds.

        :returns: :py:class:`List[ConsumedMessage]`
        """
        if not self._enabled:
            raise KafkaDisabledError

        self._subscribe(topics)

        records: typing.Dict[
            aiokafka.TopicPartition, typing.List[aiokafka.ConsumerRecord]
        ] = await self.consumer.getmany(
            timeout_ms=timeout_ms, max_records=max_batch_size
        )

        return list(map(ConsumedMessage, sum(records.values(), [])))

    async def teardown(self):
        if self._enabled:
            await self.consumer.commit()
            await self.consumer.stop()
