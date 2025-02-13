Redis
=====

Testsuite provides basic support for redis.


Environment variables
---------------------

TESTSUITE_REDIS_MASTER_PORTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override redis master ports. Two comma separated integers. Default is ``16379, 16389``.

TESTSUITE_REDIS_SENTINEL_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override sentinel server port. Default is ``26379``.

TESTSUITE_REDIS_SLAVE_PORTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override redis secondary server ports. Three comma separated integers. Default is ``16380, 16390, 16381``.

TESTSUITE_REDIS_CLUSTER_PORTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override redis cluster server ports. Six comma separated integers. Default is ``17380, 17381, 17382, 17383, 17384, 17385``.

TESTSUITE_REDIS_CLUSTER_REPLICAS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override number of replicas per master in redis cluster. Default is ``1``.

TESTSUITE_REDIS_STANDALONE_PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use to override standalone server port. Default is ``7000``.


Fixtures
--------

redis_store
~~~~~~~~~~~

Provide access to non cluster redis with sentinels via same interface as redis.StrictRedis().

.. code-block:: python

  import pytest

  pytest_plugins = [
      'testsuite.pytest_plugin',
      'testsuite.databases.redis.pytest_plugin',
  ]


  def test_redis_basic(redis_store):
      redis_store.set('somekey', 'somedata')
      assert redis_store.get('somekey') == b'somedata'


redis_cluster_store
~~~~~~~~~~~~~~~~~~~

Provide access to cluster redis via same interface as redis.RedisCluster().

.. code-block:: python

  import pytest

  pytest_plugins = [
      'testsuite.pytest_plugin',
      'testsuite.databases.redis.pytest_plugin',
  ]


  def test_redis_basic(redis_cluster_store):
      redis_cluster_store.set('somekey', 'somedata')
      assert redis_cluster_store.get('somekey') == b'somedata'


redis_standalone_store
~~~~~~~~~~~~~~~~~~~~~~

Provide access to standalone redis (no slaves or sentinels, only single master)
via same interface as redis.StrictRedis().

.. code-block:: python

  import pytest

  pytest_plugins = [
      'testsuite.pytest_plugin',
      'testsuite.databases.redis.pytest_plugin',
  ]


  def test_redis_basic(redis_standalone_store):
      redis_standalone_store.set('somekey', 'somedata')
      assert redis_standalone_store.get('somekey') == b'somedata'


redis_cluster_nodes
~~~~~~~~~~~~~~~~~~~

Provides the list of redis cluster nodes.


redis_cluster_replicas
~~~~~~~~~~~~~~~~~~~~~~

Gives the number of replicas per primary node in redis cluster.


redis_standalone_node
~~~~~~~~~~~~~~~~~~~~~~

Returns a dictionary with 'host' and 'port' values of the standalone redis.


Marks
-----

pytest.mark.redis_store
~~~~~~~~~~~~~~~~~~~~~~~

Specify custom per-test data for ``redis_store`` fixture

.. code-block:: python

  import pytest

  pytest_plugins = [
      'testsuite.pytest_plugin',
      'testsuite.databases.redis.pytest_plugin',
  ]

  @pytest.mark.redis_store(
      ['set', 'foo', 'bar'],
      ['hset', 'baz', 'quux', 'bat'],
  )
  def test_redis_marker_store(redis_store):
      assert redis_store.get('foo') == b'bar'
      assert redis_store.hgetall('baz') == {b'quux': b'bat'}

  @pytest.mark.redis_store(file='use_redis_store_file')
  def test_redis_store_file(redis_store):
      assert redis_store.get('foo') == b'store'


pytest.mark.redis_cluster_store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Specify custom per-test data for ``redis_cluster_store`` fixture

.. code-block:: python

  import pytest

  pytest_plugins = [
      'testsuite.pytest_plugin',
      'testsuite.databases.redis.pytest_plugin',
  ]

  @pytest.mark.redis_cluster_store(
      ['set', 'foo', 'bar'],
      ['hset', 'baz', 'quux', 'bat'],
  )
  def test_redis_marker_store(redis_cluster_store):
      assert redis_cluster_store.get('foo') == b'bar'
      assert redis_cluster_store.hgetall('baz') == {b'quux': b'bat'}

  @pytest.mark.redis_cluster_store(file='use_redis_store_file')
  def test_redis_store_file(redis_cluster_store):
      assert redis_cluster_store.get('foo') == b'store'



pytest.mark.redis_standalone_store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Specify custom per-test data for ``redis_standalone_store`` fixture. See above
for a usage example.
