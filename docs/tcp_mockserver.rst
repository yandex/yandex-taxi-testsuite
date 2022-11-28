Tcp mockserver
==============

Testsuite provides facility to implement custom TCP/IP mockserver. It uses
:class:`asyncio.StreamReaderProtocol` undercover, so you can write
simple server that interacts with (reader, writer). Just like with regular
:meth:`asyncio.loop.create_server`.

Example
-------

.. literalinclude:: ../tests/plugins/tcp_mockserver/test_example.py

Fixtures
--------

.. currentmodule:: testsuite.plugins.tcp_mockserver


create_tcp_mockserver
~~~~~~~~~~~~~~~~~~~~~

.. py:function:: create_tcp_mockserver(*, host='localhost', port=0, sock=None, **kwargs) -> Mockserver

   :param host: hostname to bind to, default is **localhost**
   :param port: port to bind to, default 0 binds to random port
   :param sock: socket to use instead of (hostname, port) pair
   :param kwargs: extra params are passed to :meth:`asyncio.loop.create_server`

   Returns an instance of :py:class:`Mockserver`.


   .. code-block:: python

      async with create_tcp_mockserver(host='localhost', port=0) as mockserver:
          yield mockserver



Classes
-------

.. autoclass:: Mockserver
    :members:
