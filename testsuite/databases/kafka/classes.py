import asyncio
import typing
import aiokafka
import logging
import random


class KafkaDisabledError(Exception):
    pass


class KafkaProducer:
    def __init__(self, enabled: bool, server_port: int):
        self._enabled = enabled
        self._server_port = server_port

    async def start(self):
        if self._enabled:
            self.producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=f'localhost:{self._server_port}',
            )
            await self.producer.start()

    async def send(self, topic: str, key: str, value: str):
        resp_future = await self.send_async(topic, key, value)
        await resp_future

    async def send_async(self, topic: str, key: str, value: str):
        if not self._enabled:
            raise KafkaDisabledError

        return await self.producer.send(
            topic=topic,
            value=value.encode(),
            key=key.encode(),
        )

    async def teardown(self):
        if self._enabled:
            await self.producer.stop()


class KafkaConsumer:
    class ConsumedMessage:
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

    def __init__(self, enabled: bool, server_port: int):
        self._enabled = enabled
        self._server_port = server_port
        self._subscribed_topics: typing.List[str] = list()

    async def start(self):
        if self._enabled:
            self.consumer = aiokafka.AIOKafkaConsumer(
                group_id=f'Test-group',
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
        if not self._enabled:
            raise KafkaDisabledError

        self._subscribe(topics)

        async def _do_receive():
            record: aiokafka.ConsumerRecord = await self.consumer.getone()
            return KafkaConsumer.ConsumedMessage(record)

        logging.warning('Waiting for response')
        return await asyncio.wait_for(_do_receive(), timeout=timeout)

    async def receive_batch(
        self,
        topics: typing.List[str],
        max_batch_size: int | None = None,
        timeout_ms: int = 3000,
    ) -> typing.List[ConsumedMessage]:
        if not self._enabled:
            raise KafkaDisabledError

        self._subscribe(topics)

        records: typing.Dict[
            aiokafka.TopicPartition, typing.List[aiokafka.ConsumerRecord]
        ] = await self.consumer.getmany(
            timeout_ms=timeout_ms, max_records=max_batch_size
        )

        return list(
            map(KafkaConsumer.ConsumedMessage, sum(records.values(), []))
        )

    async def teardown(self):
        if self._enabled:
            await self.consumer.commit()
            await self.consumer.stop()
