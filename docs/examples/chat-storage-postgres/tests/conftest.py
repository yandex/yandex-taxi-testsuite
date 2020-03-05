import os
import pathlib

import pytest

from testsuite.daemons import service_client
from testsuite.databases.pgsql import discover


pytest_plugins = [
    'testsuite.pytest_plugin',
    'testsuite.databases.pgsql.pytest_plugin',
]

SERVICE_BASEURL = 'http://localhost:8080/'


@pytest.fixture
async def server_client(
        service_daemon,
        service_client_options,
        ensure_daemon_started,
        mockserver,
        pgsql,
):
    await ensure_daemon_started(service_daemon)
    yield service_client.Client(SERVICE_BASEURL, **service_client_options)


@pytest.fixture(scope='session')
async def service_daemon(register_daemon_scope, service_spawner, pgsql_local):
    python_path = os.getenv('PYTHON3', 'python3')
    service_path = pathlib.Path(__file__).parent.parent
    async with register_daemon_scope(
            name='chat-storage-postgres',
            spawn=service_spawner(
                [
                    python_path,
                    str(service_path.joinpath('server.py')),
                    '--postgresql',
                    pgsql_local.get_connection_string('chat_messages'),
                ],
                check_url=SERVICE_BASEURL + 'ping',
            ),
    ) as scope:
        yield scope


@pytest.fixture(scope='session')
def pgsql_local(pgsql_local_create):
    tests_dir = pathlib.Path(__file__).parent
    sqldata_path = tests_dir.joinpath('../schemas/postgresql')
    databases = discover.find_databases('chat_storage_postgres', sqldata_path)
    return pgsql_local_create(list(databases.values()))
