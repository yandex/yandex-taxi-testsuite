def test_rabbitmq_basic(rabbitmq):
    exchange = 'testsuite_exchange'
    queue = 'testsuite_queue'
    routing_key = 'testsuite_routing_key'

    with rabbitmq.get_channel() as channel:
        channel.declare_exchange(exchange=exchange, exchange_type="fanout")
        channel.declare_queue(queue=queue)
        channel.bind_queue(
            queue=queue, exchange=exchange, routing_key=routing_key
        )
        channel.publish(
            exchange=exchange,
            routing_key=routing_key,
            body=b"hi from testsuite!",
        )

        messages = channel.consume(queue=queue, count=1)
        assert messages == [b"hi from testsuite!"]
