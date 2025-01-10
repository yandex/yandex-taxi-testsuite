RabbitMQ
========

In order to enable RabbitMQ support you have to add
``testsuite.rabbitmq.pytest_plugin`` to ``pytest_plugins`` list in your
``conftest.py``.

By default testsuite starts RabbitMQ_ service. In this case RabbitMQ installation
is required.

Currently RabbitMQ plugin uses async aio-pika_ driver.

RabbitMQ installation
---------------------

Consult official docs at https://www.rabbitmq.com/download.html

If you already have RabbitMQ installed and its location differs from
`/usr/lib/rabbitmq` please specify
``TESTSUITE_RABBITMQ_BINDIR`` environment variable accordingly.

On MacOS just install Rabbitmq with ``brew``: ``brew install rabbitmq``

Environment variables
---------------------

TESTSUITE_RABBITMQ_BINDIR
~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override rabbitmq binary dir.
Default is ``/usr/lib/rabbitmq/bin/`` for Linux
and ``/opt/homebrew/sbin/`` for MacOS

TESTSUITE_RABBITMQ_TCP_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override rabbitmq server port. Default is ``8672``.

TESTSUITE_RABBITMQ_EPMD_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override rabbitmq epmd port. Default is ``8673``.

TESTSUITE_RABBITMQ_SERVER_START_TIMEOUT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
By default testsuite will wait for up to 10s for RabbitMQ to start,
one may customize this timeout via environment variable ``TESTSUITE_RABBITMQ_SERVER_START_TIMEOUT``.

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

    async def test_rabbitmq_basic(rabbitmq):
        exchange = 'testsuite_exchange'
        queue = 'testsuite_queue'
        routing_key = 'testsuite_routing_key'

        channel = await rabbitmq.get_channel()

        async with channel:
            await channel.declare_exchange(
                exchange=exchange, exchange_type='fanout'
            )
            await channel.declare_queue(queue=queue)
            await channel.bind_queue(
                queue=queue, exchange=exchange, routing_key=routing_key
            )
            await channel.publish(
                exchange=exchange,
                routing_key=routing_key,
                body=b'hi from testsuite!',
            )

            messages = await channel.consume(queue=queue, count=1)
            assert messages == [b'hi from testsuite!']

.. _RabbitMQ: https://www.rabbitmq.com/
.. _aio-pika: https://github.com/mosquito/aio-pika

Fixtures
--------

.. currentmodule:: testsuite.databases.rabbitmq.pytest_plugin

rabbitmq
~~~~~~~~~~

.. autofunction:: rabbitmq()
  :noindex:

Classes
-------

.. currentmodule:: testsuite.databases.rabbitmq.classes

.. autoclass:: ConnectionInfo()
  :noindex:
  :members: host, tcp_port
