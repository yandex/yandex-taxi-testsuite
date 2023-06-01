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

Environment variables
---------------------

TESTSUITE_POSTGRESQL_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override Postgresql server port. Default is ``15433``.

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
