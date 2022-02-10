Spawning and accessing service
==============================

Testsuite starts process with a service being testsed.
Service must implement ``ping-url`` that returns ``200 OK`` when service is up.


.. code-block:: python

  import pytest

  SERVICE_BASEURL = 'http://localhost:8080/'


  @pytest.fixture
  async def server_client(
          ensure_daemon_started,
          create_service_client,
          mockserver,
          service_daemon,
  ):
      # Start service if not started yet
      await ensure_daemon_started(service_daemon)
      # Create service client instance
      return create_service_client(SERVICE_BASEURL)


  @pytest.fixture(scope='session')
  async def service_daemon(create_daemon_scope):
      # Generate special config for testsuite.
      service_config_path = generate_service_config()

      async with create_daemon_scope(
              args=['path-to-service-binary', '--config', service_config_path],
              check_url=SERVICE_BASEURL + 'ping',
      ) as scope:
          yield scope

Fixtures
--------

.. currentmodule:: testsuite.daemons.pytest_plugin

service_client_options
~~~~~~~~~~~~~~~~~~~~~~

Fixture that contains service client options.

service_client_default_headers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Defines default http headers to be used by service client.

register_daemon_scope
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: register_daemon_scope(name, spawn)
   :no-auto-options:

ensure_daemon_started
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: ensure_daemon_started(name)
   :no-auto-options:


create_service_client
~~~~~~~~~~~~~~~~~~~~~

.. py:function:: create_service_client

   Returns :py:class:`CreateServiceClientFixture` instance.

.. autoclass:: CreateServiceClientFixture()
   :members: __call__


create_daemon_scope
~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: create_daemon_scope

   Returns :py:class:`CreateDaemonScope` instance.

.. autoclass:: CreateDaemonScope()
   :members: __call__


service_spawner
~~~~~~~~~~~~~~~

Fixture that creates service spawner.

.. autofunction:: service_spawner(args, check_url, *, ...)
   :no-auto-options:

Classes
-------

.. currentmodule:: testsuite.daemons.service_client

.. autoclass:: Client()
    :members: __init__, post, put, patch, get, delete, options, request

.. autoclass:: AiohttpClient()
    :members: __init__, post, put, patch, get, delete, options, request
