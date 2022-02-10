import pathlib
import ssl
import typing

import pytest

from testsuite._internal import fixture_types
from testsuite.daemons import service_client

pytest_plugins = [
    'pytester',
    'testsuite.pytest_plugin',
    # Databases
    'testsuite.databases.mongo.pytest_plugin',
    'testsuite.databases.pgsql.pytest_plugin',
    'testsuite.databases.redis.pytest_plugin',
    'testsuite.databases.mysql.pytest_plugin',
]


@pytest.fixture
def mockserver_client(
        mockserver: fixture_types.MockserverFixture,
        service_client_default_headers,
        service_client_options,
) -> service_client.Client:
    return service_client.Client(
        mockserver.base_url,
        headers={
            **service_client_default_headers,
            mockserver.trace_id_header: mockserver.trace_id,
        },
        **service_client_options,
    )


@pytest.fixture
def mockserver_ssl_client(
        mockserver_ssl: fixture_types.MockserverSslFixture,
        mockserver_ssl_info: fixture_types.MockserverSslInfoFixture,
        service_client_default_headers,
        service_client_options,
):
    if not mockserver_ssl_info:
        raise RuntimeError('No https mockserver configured')
    assert mockserver_ssl_info.ssl
    ssl_context = ssl.create_default_context(
        ssl.Purpose.SERVER_AUTH, cafile=mockserver_ssl_info.ssl.cert_path,
    )
    return service_client.Client(
        mockserver_ssl.base_url,
        ssl_context=ssl_context,
        headers={
            **service_client_default_headers,
            mockserver_ssl.trace_id_header: mockserver_ssl.trace_id,
        },
        **service_client_options,
    )


@pytest.fixture
def create_service_client(
        service_client_default_headers, service_client_options,
):
    def _create_service_client(
            base_url: str,
            *,
            headers: typing.Optional[typing.Dict[str, str]] = None,
            **kwargs,
    ):
        options = {**service_client_options, **kwargs}
        return service_client.Client(
            base_url,
            headers={**service_client_default_headers, **(headers or {})},
            **options,
        )

    return _create_service_client


@pytest.fixture(scope='session')
def mongo_schema_directory():
    return pathlib.Path(__file__).parent / 'schemas/mongo'


def pytest_register_object_hooks():
    def _custom_object_hook(doc: dict):
        return '<my-custom-obj>'

    return {'$myObjHook': _custom_object_hook}


def pytest_register_matching_hooks():
    def _custom_operator_match(doc: dict):
        return '<my-custom-type>'

    return {'custom-matching': _custom_operator_match}
