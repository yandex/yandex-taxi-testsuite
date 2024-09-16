Kafka
========

In order to enable Kafka support you have to add
``testsuite.kafka.pytest_plugin`` to ``pytest_plugins`` list in your
``conftest.py``.

By default testsuite starts Kafka_ service. In this case Kafka installation
is required.

Currently Kafka plugin uses sync confluent-kafka-python_ driver.

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override Kafka controller port. Default is ``9093``.

TESTSUITE_KAFKA_SERVER_START_TIMEOUT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
By default testsuite will wait for up to 20s for Kafka to start,
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
``TESTSUITE_RABBITMQ_TCP_PORT`` and pytest option ``--rabbitmq=1``
and see if it works.

Usage example
-------------

.. code-block:: python

    async def test_kafka_basic(kafka_producer):
        await kafka_producer.produce('Test-topic', 'test-key', 'test-value')

.. _Kafka: https://kafka.apache.org/
.. _confluent-kafka-python: https://github.com/confluentinc/confluent-kafka-python

Fixtures
--------

.. currentmodule:: testsuite.databases.kafka.pytest_plugin

kafka_producer
~~~~~~~~~~

.. autofunction:: kafka_producer()
  :noindex:
