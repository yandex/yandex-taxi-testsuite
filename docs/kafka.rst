Kafka
========

In order to enable Kafka support you have to add
``testsuite.kafka.pytest_plugin`` to ``pytest_plugins`` list in your
``conftest.py``.

By default testsuite starts Kafka_ service. In this case Kafka installation
is required.

Currently Kafka plugin uses async aiokafka_ driver.

Kafka installation
---------------------

Consult official docs at https://kafka.apache.org/quickstart

If you already have Kafka installed and its location differs from
`/etc/kafka` please specify
``KAFKA_HOME`` environment variable accordingly.

Environment variables
---------------------

KAFKA_HOME
~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override Kafka binary dir. Default is ``/etc/kafka``

TESTSUITE_KAFKA_SERVER_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override Kafka server port. Default is ``9092``.

TESTSUITE_KAFKA_CONTROLLER_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override Kafka controller port. Default is ``9093``.

TESTSUITE_KAFKA_SERVER_START_TIMEOUT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
By default testsuite will wait for up to 10s for Kafka to start,
one may customize this timeout via environment variable ``TESTSUITE_KAFKA_SERVER_START_TIMEOUT``.

Customize ports
---------------

Testsuite may start Kafka with custom ports if
``TESTSUITE_KAFKA_SERVER_PORT`` or ``TESTSUITE_KAFKA_CONTROLLER_PORT``
environment variables are specified.

Use external instance
---------------------

Usage of external instance is not officially supported for now,
but if your instance is local you may try setting environment variable
``TESTSUITE_KAFKA_SERVER_PORT`` and pytest option ``--kafka=1``
and see if it works.

Usage example
-------------

.. code-block:: python

      async def test_kafka_producer_consumer_chain(kafka_producer, kafka_consumer):
          TOPIC = 'Test-topic-chain'
          KEY = 'test-key'
          MESSAGE = 'test-message'

          await kafka_producer.send(TOPIC, KEY, MESSAGE)

          consumed_message = await kafka_consumer.receive_one([TOPIC])

          assert consumed_message.topic == TOPIC
          assert consumed_message.key == KEY
          assert consumed_message.value == MESSAGE

.. _Kafka: https://kafka.apache.org/
.. _aiokafka: https://github.com/aio-libs/aiokafka

Fixtures
--------

.. currentmodule:: testsuite.databases.kafka.pytest_plugin

kafka_producer
~~~~~~~~~~~~~~

.. autofunction:: kafka_producer()
  :noindex:

kafka_consumer
~~~~~~~~~~~~~~

.. autofunction:: kafka_consumer()
  :noindex:


Classes
-------

.. currentmodule:: testsuite.databases.kafka.classes

.. autoclass:: KafkaProducer()
  :members: send, send_async

.. autoclass:: KafkaConsumer()
  :members: receive_one, receive_batch
