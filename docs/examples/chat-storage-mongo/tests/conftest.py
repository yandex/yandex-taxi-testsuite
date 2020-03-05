import os
import pathlib

import pytest

from testsuite.daemons import service_client

pytest_plugins = [
    'testsuite.pytest_plugin',
    'testsuite.databases.mongo.pytest_plugin',
]

SERVICE_BASEURL = 'http://localhost:8080/'

MONGO_COLLECTIONS = {
    'messages': {
        'settings': {
            'collection': 'messages',
            'connection': 'example',
            'database': 'chat_db',
        },
        'indexes': [{'key': 'created'}],
    },
}


@pytest.fixture
async def server_client(
        service_daemon, service_client_options, ensure_daemon_started, mongodb,
):
    await ensure_daemon_started(service_daemon)
    yield service_client.Client(SERVICE_BASEURL, **service_client_options)


# remove scope=session to restart service on each test
@pytest.fixture(scope='session')
async def service_daemon(register_daemon_scope, service_spawner, mongo_host):
    python_path = os.getenv('PYTHON3', 'python3')
    service_path = pathlib.Path(__file__).parent.parent
    async with register_daemon_scope(
            name='chat-storage-mongo',
            spawn=service_spawner(
                [
                    python_path,
                    str(service_path.joinpath('server.py')),
                    '--mongo-uri',
                    mongo_host + '?retryWrites=false',
                ],
                check_url=SERVICE_BASEURL + 'ping',
            ),
    ) as scope:
        yield scope


@pytest.fixture(scope='session')
def mongodb_settings():
    return MONGO_COLLECTIONS
