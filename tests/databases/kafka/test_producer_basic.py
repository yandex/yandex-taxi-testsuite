import asyncio


async def test_kafka_producer_basic(kafka_producer):
    await kafka_producer.send('Test-topic', 'test-key', 'test-message')


async def test_kafka_producer_many_sends(kafka_producer):
    TOPIC = 'Test-topic'
    SEND_COUNT = 10
    for send in range(SEND_COUNT):
        await kafka_producer.send(
            TOPIC, f'test-key-{send}', f'test-message-{send}'
        )


async def test_kafka_producer_many_send_async(kafka_producer):
    TOPIC = 'Test-topic'
    SEND_COUNT = 100
    send_futures = []
    for send in range(SEND_COUNT):
        send_futures.append(
            await kafka_producer.send_async(
                TOPIC, f'test-key-{send}', f'test-message-{send}'
            )
        )
    await asyncio.wait(send_futures)


async def test_kafka_producer_large_topic(kafka_producer):
    TOPIC = 'Large-Topic'
    PARTITION_COUNT = 7

    for partition in range(PARTITION_COUNT):
        await kafka_producer.send(
            TOPIC,
            f'key-to-{partition}',
            f'message-to-{partition}',
            partition=partition,
        )
