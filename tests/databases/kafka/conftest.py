import pytest

pytest_plugins = [
    'testsuite.pytest_plugin',
    'testsuite.databases.kafka.pytest_plugin',
]


@pytest.fixture(scope='session')
def kafka_custom_topics() -> dict[str, int]:
    return {'Large-Topic': 7}
