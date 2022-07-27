RabbitMQ
========

.. contents::
   :depth: 2
   :local:

In order to enable RabbitMQ support you have to add
``testsuite.rabbitmq.pytest_plugin`` to ``pytest_plugins`` list in your
``conftest.py``.

By default testsuite starts RabbitMQ_ service. In this case RabbitMQ installation
is required.

Currently RabbitMQ plugin uses blocking adapters from pika_ driver.

RabbitMQ installation
---------------------

Consult official docs at https://www.rabbitmq.com/download.html

If you already have RabbitMQ installed and its location differs from
`/usr/lib/rabbitmq` please specify 
``TESTSUITE_RABBITMQ_BINDIR`` environment variable accordingly.

Customize ports
---------------

Testsuite may start RabbitMQ with custom ports if 
``TESTSUITE_RABBITMQ_TCP_PORT`` or ``TESTSUITE_RABBITMQ_EPMD_PORT``
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

.. _RabbitMQ: https://www.rabbitmq.com/
.. _pika: https://pika.readthedocs.io/en/stable/

Fixtures
--------

.. currentmodule:: testsuite.rabbitmq.pytest_plugin

rabbitmq
~~~~~~~~~~

.. autofunction:: rabbitmq()
  :noindex:

Classes
-------

.. currentmodule:: testsuite.rabbitmq.classes

.. autoclass:: ConnectionInfo()
  :noindex:
  :members: host, tcp_port