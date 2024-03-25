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

Environment variables
---------------------

TESTSUITE_MONGO_CONFIG_SERVER_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override mongo config server port. Default is ``27118``.

TESTSUITE_MONGOS_PORT
~~~~~~~~~~~~~~~~~~~~~

Use to override mongos port. Default is ``27217``.

TESTSUITE_MONGO_SHARD_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override mongo shard port. Default is ``27119``.

TESTSUITE_MONGO_RS_INSTANCE_COUNT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Replica set instances count, one instance is started by default.

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


Marks
-----

pytest.mark.filldb
~~~~~~~~~~~~~~~~~~

Specify custom per-test collection data file prefix.

.. py:function:: pytest.mark.filldb(**suffixes)

    :param suffixes: collection suffixes map, e.g.
                     ``{'collection': 'suffix', ...}``


In the following example plugin will look for filename
``db_collection_name_foo.json``:

.. code-block:: python

   @pytest.mark.filldb(collection_name='foo')
   def test_foo(...):


pytest.mark.nofilldb
~~~~~~~~~~~~~~~~~~~~

Disables database loading.

.. py:function:: pytest.mark.nofilldb


Classes
-------

.. autoclass:: testsuite.databases.mongo.connection.ConnectionInfo()
  :members: dbname, host, port, retry_writes, get_uri
