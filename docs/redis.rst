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
