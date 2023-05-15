Database support
****************

.. contents::
   :depth: 2
   :local:

Database plugins can start and stop database process.
You can configure it to use existing database.

Testsuite clears database and applies data fixtures before each test ensure
database in known state.

Data fixtures are loaded via staatic files, see :ref:`staticfiles`.

Common database marks
=====================

pytest.mark.nofilldb
---------------------

Disables database loading.

.. py:function:: pytest.mark.nofilldb


.. include:: mongo.rst
.. include:: postgresql.rst
.. include:: mysql.rst
.. include:: redis.rst
.. include:: clickhouse.rst
.. include:: rabbitmq.rst
