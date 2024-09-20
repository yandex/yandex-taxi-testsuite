import typing

import pytest


@pytest.fixture(scope='session')
def kafka_custom_topics() -> typing.Dict[str, int]:
    return {'Large-Topic': 7}
