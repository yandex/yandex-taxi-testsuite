Service logs
************

Service logs formatter
======================

.. currentmodule:: testsuite.plugins.servicelogs

Testsuite provides plugin to pretty-print service logs (colorize, simplify, etc...).
It only reads logfiles when testcase fails with no extra overhead.

It also support live-logs when pytest is started with `-s` option. In this
case logs would be printed from special thread.

Fixtures
--------

servicelogs_register_logfile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: servicelogs_register_logfile(path: pathlib.Path, *, title: str, formatter_factory)

   Registers logfile into testsuite.

   :param path: path to logfile
   :param title: logfile name
   :param formatter_factory: Log formatter factory


   .. code-block:: python

      async def test_formatter(servicelogs_register_logfile):
          logfile = pathlib.Path(...)

          def formatter_factory():
              # formatter may have its own context
              def formatter(line: bytes) -> str | None:
                  return line.encode('utf-8')
              return formatter

          servicelogs_register_logfile(
              logfile, title='My service logs',
              formatter_factory=formatter_factory
          )

servicelogs_register_flusher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: servicelogs_register_flusher(func)

   Registers async function that would be called to flush service buffer in
   case of failure.

   .. code-block:: python

      async def test_flusher(servicelogs_register_flusher):
          @servicelogs_register_flusher
          async def flusher():
              ...

service_logs_update_position
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: service_logs_update_position

   Seeks all registered logfiles to the end.
   Useful to skip initial service logs.


Options
-------

--service-livelogs-disable
~~~~~~~~~~~~~~~~~~~~~~~~~~

Disables service live logs.

Service logs capture
====================

.. currentmodule:: testsuite.logcapture

.. automodule:: testsuite.logcapture

.. autoclass:: LogLevel
  :members: from_string, TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL, NONE

.. autoclass:: CaptureServer()
  :members: __init__, start, wait_for_client, capture, default_log_level, getsocknames

.. autoclass:: Capture
  :members: select, subscribe
