MySQL
=====

In order to enable mysql support you have to add
``testsuite.database.mysql_plugin`` to ``pytest_plugins`` list in your
``conftest.py`` file and configure MySQL schemas location.

By default testsuite starts MySQL_ service. In this case MySQL installation
is required.

Currently mysql plugin uses synchronous pymysql_ driver.

MySQL plugin creates database schema once. And then populates database
with data fixtures on each test. It looks for database fixtures by the
following names:

* file ``my_DBNAME.sql``
* directory ``my_DBNAME/``

Customize port
--------------

Testsuite may start MySQL with custom port, if ``TESTSUITE_MYSQL_PORT``
environment variable is specified

Use external instance
---------------------

You can force it to use your own mysql installation with command-line option
``--mysql=mysql://user:password@hostname/``.


Example integration
-------------------

.. code-block:: python

  from testsuite.databases.mysql import discover

  @pytest.fixture(scope='session')
  def mysql_local():
      return discover.find_schemas([SCHEMAS_DIR])


Database access example
-----------------------

.. code-block:: python

  def test_read_from_database(mysql):
      cursor = mysql['chat_messages'].cursor()
      cursor.execute(
          'SELECT username, text FROM messages WHERE id = %s', (data['id'],),
      )
      record = cursor.fetchone()
      assert record == ('foo', 'bar')

.. _MySQL: https://dev.mysql.com/
.. _pymysql: https://github.com/PyMySQL/PyMySQL


Functions
---------

find_schemas
~~~~~~~~~~~~

.. currentmodule:: testsuite.databases.mysql.discover

.. autofunction:: find_schemas

Fixtures
--------

.. currentmodule:: testsuite.databases.mysql.pytest_plugin

mysql
~~~~~

.. autofunction:: mysql()
  :noindex:

mysql_local
~~~~~~~~~~~

.. autofunction:: mysql_local()
  :noindex:


mysql_conninfo
~~~~~~~~~~~~~~

.. autofunction:: mysql_conninfo()
  :noindex:


Marks
-----

pytest.mark.mysql
~~~~~~~~~~~~~~~~~

.. py:function:: pytest.mark.mysql(dbname, *, files=(), directories=(), queries=()):

   Use this mark to specify extra data fixtures in a per-test manner.

   :param dbname: Database name.
   :param files: List of filenames to apply to the database.
   :param directories: List of directories to apply to the database.
   :param queries: List of queries to apply to the database.

Classes
-------

.. currentmodule:: testsuite.databases.mysql.control

.. autoclass:: ConnectionWrapper()
  :noindex:
  :members: conninfo, cursor

.. currentmodule:: testsuite.databases.mysql.classes

.. autoclass:: ConnectionInfo()
  :noindex:
  :members: port, hostname, user, password, dbname, replace
