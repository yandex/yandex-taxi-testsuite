ClickHouse
==========

In order to enable clickhouse support you have to add
``testsuite.databases.clickhouse.pytest_plugin`` to ``pytest_plugins`` list in your
``conftest.py`` file and configure ClickHouse schemas location.

By default testsuite starts ClickHouse_ service. In this case ClickHouse installation
is required.

Currently clickhouse plugin uses synchronous clickhouse-driver_ driver.

ClickHouse plugin creates database schema once. And then populates database
with data fixtures on each test. It looks for database fixtures by the
following names:

* file ``ch_DBNAME.sql``
* directory ``ch_DBNAME/``


ClickHouse installation
-----------------------
For debian please run these commands:

.. code-block:: bash

  sudo apt update && apt install clickhouse-common-static 

(https://clickhouse.com/docs/en/getting-started/install/#packages),

For macos follow instructions at https://clickhouse.com/docs/en/getting-started/install/#from-binaries-non-linux

If you already have clickhouse installed, please symlink it to ``/usr/bin/clickhouse``

Customize ports
---------------

Testsuite may start ClickHouse with custom ports, if 
``TESTSUITE_CLICKHOUSE_SERVER_TCP_PORT`` or ``TESTSUITE_CLICKHOUSE_SERVER_HTTP_PORT``
environment variables are specified.

Use external instance
---------------------

Usage of external installation is not supported for now.


Example integration
-------------------

.. code-block:: python

  from testsuite.databases.clickhouse import discover

  @pytest.fixture(scope='session')
  def clickhouse_local():
      return discover.find_schemas([SCHEMAS_DIR])


Database access example
-----------------------

.. code-block:: python

  def test_read_from_database(clickhouse):
      connection = clickhouse['chat_messages']
      result = connection.execute('SELECT * FROM system.numbers LIMIT 5')
      assert result == [(0,), (1,), (2,), (3,), (4,)]

.. _ClickHouse: https://clickhouse.com/
.. _clickhouse-driver: https://github.com/mymarilyn/clickhouse-driver


Functions
---------

find_schemas
~~~~~~~~~~~~

.. currentmodule:: testsuite.databases.clickhouse.discover

.. autofunction:: find_schemas

Fixtures
--------

.. currentmodule:: testsuite.databases.clickhouse.pytest_plugin

clickhouse
~~~~~~~~~~

.. autofunction:: clickhouse()
  :noindex:

clickhouse_local
~~~~~~~~~~~~~~~~

.. autofunction:: clickhouse_local()
  :noindex:


clickhouse_conn_info
~~~~~~~~~~~~~~~~~~~~

.. autofunction:: clickhouse_conn_info()
  :noindex:


Marks
-----

pytest.mark.clickhouse
~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: pytest.mark.clickhouse(dbname, *, files=(), directories=(), queries=()):

   Use this mark to specify extra data fixtures in a per-test manner.

   :param dbname: Database name.
   :param files: List of filenames to apply to the database.
   :param directories: List of directories to apply to the database.
   :param queries: List of queries to apply to the database.

Classes
-------

.. currentmodule:: testsuite.databases.clickhouse.classes

.. autoclass:: ConnectionInfo()
  :noindex:
  :members: host, tcp_port, http_port, dbname
