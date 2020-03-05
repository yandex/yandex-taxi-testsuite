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

mongo_host
~~~~~~~~~~

.. autofunction:: mongo_host()
   :no-auto-options:

   Returns mongodb connection string, e.g.: ``mongodb://localhost:27119/``


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


PostgreSQL
==========

In ordrer to enable mongo support you have to add
``testsuite.database.mongo.pgsql_plugin`` to ``pytest_plugins`` list in your
``conftest.py`` file and configure mongodb collections.

By default testsuite starts PostgreSQL_ sharded cluster. In this case
PostgreSQL installation is required.
You can force it to use your own mongo installation with command-line option
``--postgresql=postgresql://db-postgresql/``.

Currently mongo plugin uses synchronous psycopg2_ driver.

Pgsql plugin creates database schema once. And then populates database
with data fixtures on each test. It looks for database fixtures by the
following names:

* file ``pg_DBNAME.sql``
* directory ``pg_DBNAME/``

Example integration:

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
      databases = discover.find_databases('service_name', sqldata_path)
      return pgsql_local_create(list(databases.values()))


.. _PostgreSQL: https://www.postgresql.org/
.. _psycopg2: https://pypi.org/project/psycopg2/


Functions
---------

find_databases
~~~~~~~~~~~~~~

.. currentmodule:: testsuite.databases.pgsql.discover

.. autofunction:: find_databases


Fixtures
--------

.. currentmodule:: testsuite.databases.pgsql.pytest_plugin

pgsql
~~~~~

.. autofunction:: pgsql()


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
  :members: get_connection_string


Redis
=====

Testsuite provides basic support for redis.

