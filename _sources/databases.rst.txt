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


Mongo
=====

.. currentmodule:: testsuite.databases.mongo.pytest_plugin

In ordrer to enable mongo support you have to add
``testsuite.database.mongo.pytest_plugin`` to ``pytest_plugins`` list in your
``conftest.py`` file and configure mongodb collections.

By default testsuite starts mongodb sharded cluster. In this case mongodb_
installation is required.

Testsuite may start mongodb with custom ports, if following environment
variables are specified:

- ``TESTSUITE_MONGO_CONFIG_SERVER_PORT``
- ``TESTSUITE_MONGOS_PORT``
- ``TESTSUITE_MONGO_SHARD_PORT``

You can force it to use your own mongo installation with command-line option
``--mongo=mongodb://host:port/``.

Mongodb plugins re-fills the whole database with data on each test.
It looks for data fixture static files using ``db_collection_name.json``
pattern. If no file is found collection is empty.

Currently mongo plugin uses synchronous pymongo_ driver.

Example integration:

.. code-block:: python

  pytest_plugins = [
      'testsuite.pytest_plugin',
      'testsuite.databases.mongo.pytest_plugin',
  ]

  MONGO_COLLECTIONS = {
      'example_collection': {
          'settings': {
              'collection': 'example_collection',
              'connection': 'example',
              'database': 'example_db',
          },
          'indexes': [],
      },
  }

  @pytest.fixture(scope='session')
  def mongodb_settings():
      return MONGO_COLLECTIONS

.. _mongodb: https://www.mongodb.com/
.. _pymongo: https://api.mongodb.com/python/current/

Fixtures
--------

mongodb
~~~~~~~

.. autofunction:: mongodb()
   :no-auto-options:

   Returns :py:class:`CollectionWrapper` instance. Collection can be accessed
   by name, e.g.:

   .. code-block:: python

      def test_foo(mongodb):
          doc = mongodb.collection_name.find_one({'_id': 123})
          assert doc == {...}

   :py:class:`pymongo.collection.Collection` instance is returned.

mongo_connection_info
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: mongo_connection_info()
   :no-auto-options:

   Returns an instance of class
   :py:class:`testsuite.databases.mongo.connection.ConnectionInfo`


mongo_host
~~~~~~~~~~

.. autofunction:: mongo_host()
   :no-auto-options:

   This fixture is obsolete. Use ``mongo_connection_info`` fixture instead.

   Returns mongodb connection string, e.g.:
   ``mongodb://localhost:27119/?retryWrites=false``

   ``retryWrites`` parameter can be changed through ``pytest.ini`` via
   ``mongo-retry-writes`` boolean setting. Default value is ``false`` which is
   required since mongodb version 4.2 and pymongo version 3.9.

Marks
-----

pytest.mark.filldb
~~~~~~~~~~~~~~~~~~

Specify custom per-test collection data file prefix.

.. py:function:: pytest.mark.filldb(**suffixes)

    :param suffixes: collection suffixes map, e.g.
                     ``{'collection': 'suffix', ...}``

I
In the following example plugin will look for filename
``db_collection_name_foo.json``:

.. code-block:: python

   @pytest.mark.filldb(collection_name='foo')
   def test_foo(...):

Classes
-------

.. autoclass:: testsuite.databases.mongo.connection.ConnectionInfo()
  :members: dbname, host, port, retry_writes, get_uri

PostgreSQL
==========

In order to enable postgres support you have to add
``testsuite.database.pgsql_plugin`` to ``pytest_plugins`` list in your
``conftest.py`` file and configure postgresql schemas location.

By default testsuite starts PostgreSQL_ service. In this case
PostgreSQL installation is required.

Currently pgsql plugin uses synchronous psycopg2_ driver.

Pgsql plugin creates database schema once. And then populates database
with data fixtures on each test. It looks for database fixtures by the
following names:

* file ``pg_DBNAME.sql``
* directory ``pg_DBNAME/``

Customize port
--------------

Testsuite may start postgres with custom port, if ``TESTSUITE_POSTGRESQL_PORT``
environment variable is specified

Use external instance
---------------------

You can force it to use your own postgres installation with command-line option
``--postgresql=postgresql://db-postgresql/``.

Reuse database between simultaneous sessions
--------------------------------------------

In general, testsuite does not support running simultaneous sessions, except
when testsuite is started with ``--postgresql-keep-existing-db`` or
``--service-runner-mode`` flag.

In service runner mode testsuite starts the service and waits indefinitely
so that developer can attach to running service with debugger.

If one session in service runner mode creates database and applies schemas,
then the next one will skip applying schemas on initialization, unless schemas
were modified since then.

Example integration
-------------------

.. code-block:: python

  from testsuite.databases.pgsql import discover

  pytest_plugins = [
      'testsuite.pytest_plugin',
      'testsuite.databases.pgsql.pytest_plugin',
  ]


  @pytest.fixture(scope='session')
  def pgsql_local(pgsql_local_create):
      tests_dir = pathlib.Path(__file__).parent
      sqldata_path = tests_dir.joinpath('../schemas/postgresql')
      databases = discover.find_schemas('service_name', [sqldata_path])
      return pgsql_local_create(list(databases.values()))

Database access example
-----------------------

.. code-block:: python

  def test_read_from_database(pgsql):
      cursor = pgsql['chat_messages'].cursor()
      cursor.execute(
          'SELECT username, text FROM messages WHERE id = %s', (data['id'],),
      )
      record = cursor.fetchone()
      assert record == ('foo', 'bar')

.. _PostgreSQL: https://www.postgresql.org/
.. _psycopg2: https://pypi.org/project/psycopg2/


Functions
---------

find_schemas
~~~~~~~~~~~~

.. currentmodule:: testsuite.databases.pgsql.discover

.. autofunction:: find_schemas


Fixtures
--------

.. currentmodule:: testsuite.databases.pgsql.pytest_plugin

pgsql
~~~~~

.. autofunction:: pgsql()


pgsql_cleanup_exclude_tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: pgsql_cleanup_exclude_tables()

    Redefine this fixture when you don't need to clean some tables.
    For example postgis create table with spatial reference systems. To use postgis you need to
    add this fixture with spatial_ref_sys table.

    .. code-block:: python

        @pytest.fixture(scope='session')
        def pgsql_cleanup_exclude_tables():
            return frozenset({'public.spatial_ref_sys'})


pgsql_local
~~~~~~~~~~~

.. autofunction:: pgsql_local()


pgsql_local_create
~~~~~~~~~~~~~~~~~~

.. autofunction:: pgsql_local_create(databases)


Marks
-----

pytest.mark.pgsql
~~~~~~~~~~~~~~~~~

.. py:function:: pytest.mark.pgsql(dbname, files=(), directories=(), queries=())

   Use this mark to override specify extra data fixtures in a per-test manner.

   :param dbname: Database name.
   :param files: List of filenames to apply to the database.
   :param directories: List of directories to apply to the database.
   :param directories: List of queries to apply to the database.


Classes
-------

.. autoclass:: ServiceLocalConfig()
  :members: __getitem__

.. autoclass:: testsuite.databases.pgsql.connection.PgConnectionInfo()
  :members: get_dsn, get_uri, replace

.. autoclass:: testsuite.databases.pgsql.control.PgDatabaseWrapper()
  :members: conn, conninfo, cursor, dict_cursor

.. include:: mysql.rst

Redis
=====

Testsuite provides basic support for redis.

Testsuite may start redis with custom ports, if following environment variables
are specified:

- ``TESTSUITE_REDIS_MASTER_PORTS`` - if set, must be two comma separated
  integers
- ``TESTSUITE_REDIS_SENTINEL_PORT`` - if set, must be integer
- ``TESTSUITE_REDIS_SLAVE_PORTS`` - if set must be three comma separated
  integers

.. include:: clickhouse.rst
