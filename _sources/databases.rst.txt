Database support
****************

Database plugins can start and stop database process.
You can configure it to use existing database.

Testsuite clears database and applies data fixtures before each test ensure
database in known state.

Data fixtures are loaded via staatic files, see :ref:`staticfiles`.


.. toctree::
   :maxdepth: 2

   mongo.rst
   postgresql.rst
   mysql.rst
   redis.rst
   clickhouse.rst
   rabbitmq.rst
