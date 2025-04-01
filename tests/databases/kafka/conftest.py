import pytest


@pytest.fixture(scope='session')
def kafka_custom_topics() -> dict[str, int]:
    return {'Large-Topic': 7}
