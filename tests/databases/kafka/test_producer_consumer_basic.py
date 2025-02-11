import logging
import typing


async def test_kafka_producer_consumer_chain(kafka_producer, kafka_consumer):
    TOPIC = 'Test-topic-chain'
    KEY = 'test-key'
    MESSAGE = 'test-message'

    await kafka_producer.send(TOPIC, KEY, MESSAGE)

    consumed_message = await kafka_consumer.receive_one([TOPIC])

    assert consumed_message.topic == TOPIC
    assert consumed_message.key == KEY
    assert consumed_message.value == MESSAGE


async def test_kafka_producer_consumer_chain_many_messages(
    kafka_producer, kafka_consumer
):
    TOPIC = 'Test-topic-chain'
    SEND_COUNT = 10
    BATCH_SIZE = 5

    for send in range(SEND_COUNT):
        await kafka_producer.send(
            TOPIC, f'test-key-{send}', f'test-message-{send}'
        )

    sends_received: typing.Set[int] = set()

    while len(sends_received) < SEND_COUNT:
        consumed_messages = await kafka_consumer.receive_batch(
            topics=[TOPIC], max_batch_size=BATCH_SIZE
        )
        logging.info('Received batch of %d messages', len(consumed_messages))
        for message in consumed_messages:
            sends_received.add(int(message.key.split('-')[-1]))


async def test_kafka_producer_consumer_chain_many_topics(
    kafka_producer, kafka_consumer
):
    TOPIC_COUNT = 3
    TOPICS = [f'Test-topic-chain-{i}' for i in range(TOPIC_COUNT)]
    SEND_PER_TOPIC_COUNT = 10
    MESSAGE_COUNT = TOPIC_COUNT * SEND_PER_TOPIC_COUNT
    BATCH_SIZE = 5

    for i, topic in enumerate(TOPICS):
        for send in range(SEND_PER_TOPIC_COUNT):
            send_number = i * SEND_PER_TOPIC_COUNT + send
            await kafka_producer.send(
                topic, f'test-key-{send_number}', f'test-message-{send_number}'
            )

    sends_received: typing.Set[int] = set()

    while len(sends_received) < MESSAGE_COUNT:
        consumed_messages = await kafka_consumer.receive_batch(
            topics=TOPICS, max_batch_size=BATCH_SIZE
        )
        logging.info('Received batch of %d messages', len(consumed_messages))
        for message in consumed_messages:
            sends_received.add(int(message.key.split('-')[-1]))


async def test_kafka_producer_consumer_chain_bytes(
    kafka_producer, kafka_consumer
):
    TOPIC = 'Test-topic-chain'
    KEY = b'test-key'
    MESSAGE = b'test-message'

    await kafka_producer.send(TOPIC, KEY, MESSAGE)

    consumed_message = await kafka_consumer.receive_one([TOPIC])

    assert consumed_message.topic == TOPIC
    assert consumed_message.key_raw == KEY
    assert consumed_message.value_raw == MESSAGE
