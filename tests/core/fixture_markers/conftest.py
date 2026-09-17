import pytest
from fixture_markers_plugin import visibility


@pytest.fixture(scope='session')
@visibility('conftest')
def conftest_visibility():
    return 'conftest'
