async def test_kafka_basic(kafka_producer):
    await kafka_producer.produce('Test-topic', 'test-key', 'test-message')
