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
``/etc/kafka`` please specify
``KAFKA_HOME`` environment variable accordingly.

On MacOS just install Kafka with ``brew``: ``brew install kafka``

Installed Kafka **must** support KRaft_ protocol.

Environment variables
---------------------

KAFKA_HOME
~~~~~~~~~~

Use to override Kafka binaries dir.
Default is ``/etc/kafka`` for Linux and ``/opt/homebrew/opt/kafka/libexec`` for MacOS

TESTSUITE_KAFKA_SERVER_HOST
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override Kafka server host. Default is ``localhost``.

TESTSUITE_KAFKA_SERVER_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override Kafka server port. Default is ``9099``.

TESTSUITE_KAFKA_CONTROLLER_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override Kafka controller port. Default is ``9100``.

TESTSUITE_KAFKA_SERVER_START_TIMEOUT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default testsuite will wait for up to 10s for Kafka to start,
one may customize this timeout via environment variable ``TESTSUITE_KAFKA_SERVER_START_TIMEOUT``.

TESTSUITE_KAFKA_CUSTOM_TOPICS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All topics in tests are created automatically by Kafka broker in runtime with **only 1 partition**.
To create topics with several partitions, either specify ``TESTSUITE_KAFKA_CUSTOM_TOPICS`` environment
variable with the ``,`` separated list of topic to partitions count mapping or override the ``kafka_custom_topics`` fixture.
For example, ``TESTSUITE_KAFKA_CUSTOM_TOPICS=large-topic-1:7,large-topic-2:20``
creates topic ``large-topic-1`` with 7 partitions and ``large-topic-2`` with 20 partitions.

Customize ports
---------------

Testsuite may start Kafka with custom ports if
``TESTSUITE_KAFKA_SERVER_PORT`` or ``TESTSUITE_KAFKA_CONTROLLER_PORT``
environment variables are specified.

Use external instance
---------------------

If your instance is local you may try setting environment variable
``TESTSUITE_KAFKA_SERVER_PORT`` and pytest option ``--kafka=1``
and see if it works.

P.S. Topics creation remains on the user's side.

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
.. _KRaft: https://developer.confluent.io/learn/kraft/

Example integration
-------------------

.. code-block:: python

  pytest_plugins = [
      'testsuite.pytest_plugin',
      'testsuite.databases.kafka.pytest_plugin',
  ]

  KAFKA_CUSTOM_TOPICS = {
      'Large-topic-1': 7,
      'Large-topic-2': 3,
  }

  @pytest.fixture(scope='session')
  def kafka_custom_topics():
      return KAFKA_CUSTOM_TOPICS

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

kafka_custom_topics
~~~~~~~~~~~~~~~~~~~

.. autofunction:: kafka_custom_topics()
  :noindex:

kafka_local
~~~~~~~~~~~~~~~~~~~

.. autofunction:: kafka_local()
  :noindex:


Classes
-------

.. currentmodule:: testsuite.databases.kafka.classes

.. autoclass:: KafkaProducer()
  :members: send, send_async

.. autoclass:: KafkaConsumer()
  :members: receive_one, receive_batch

.. autoclass:: ConsumedMessage()
  :members: topic, key, value, partition, offset
