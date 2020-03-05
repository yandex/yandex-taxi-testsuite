Spawning and accessing service
==============================

Testsuite starts process with a service being testsed.
Service must implement ``ping-url`` that returns ``200 OK`` when service is up.


.. code-block:: python

  import pytest

  from testsuite.daemons import service_client

  SERVICE_BASEURL = 'http://localhost:8080/'


  @pytest.fixture
  async def server_client(
          service_daemon,
          service_client_options,
          ensure_daemon_started,
          mockserver,
  ):
      await ensure_daemon_started(service_daemon)
      yield service_client.Client(SERVICE_BASEURL, **service_client_options)


  @pytest.fixture(scope='session')
  async def service_daemon(register_daemon_scope, service_spawner):
      # Generate special config for testsuite.
      service_config_path = generate_service_config()

      async with register_daemon_scope(
              name='yandex-taxi-test-service',
              spawn=service_spawner(
                  ['path-to-service-binary', '--config', service_config_path],
                  check_url=SERVICE_BASEURL + 'ping',
              ),
      ) as scope:
          yield scope

Fixtures
--------

.. currentmodule:: testsuite.daemons.pytest_plugin

service_client_options
~~~~~~~~~~~~~~~~~~~~~~

Fixture that contains service client options.

register_daemon_scope
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: register_daemon_scope(name, spawn)
   :no-auto-options:

ensure_daemon_started
~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: ensure_daemon_started(name)
   :no-auto-options:


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
