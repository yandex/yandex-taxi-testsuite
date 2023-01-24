async def test_rabbitmq_basic(rabbitmq):
    exchange = 'testsuite_exchange'
    queue = 'testsuite_queue'
    routing_key = 'testsuite_routing_key'

    channel = await rabbitmq.get_channel()

    async with channel:
        await channel.declare_exchange(
            exchange=exchange,
            exchange_type='fanout',
        )
        await channel.declare_queue(queue=queue)
        await channel.bind_queue(
            queue=queue,
            exchange=exchange,
            routing_key=routing_key,
        )
        await channel.publish(
            exchange=exchange,
            routing_key=routing_key,
            body=b'hi from testsuite!',
        )

        messages = await channel.consume(queue=queue, count=1)
        assert messages == [b'hi from testsuite!']
