from pika.adapters.blocking_connection import BlockingChannel

def test_rabbitmq_basic(rabbitmq):
    channel : BlockingChannel = rabbitmq.channel()
    channel.exchange_declare(exchange='testsuite', exchange_type='fanout')
    channel.queue_declare(queue='testsuite')
    channel.queue_bind(queue='testsuite', exchange='testsuite', routing_key='testsuite')
    channel.basic_publish(exchange='testsuite', routing_key='testsuite', body='hi!')

    for _, _, body in channel.consume(queue='testsuite'):
        assert body == b'hi!'
        break

    channel.cancel()
