import pytest


@pytest.fixture(scope='session')
def testsuite_traceid_generator():
    def gen():
        return 'foo'

    return gen


def test_override(testsuite_traceid_manager):
    assert testsuite_traceid_manager.trace_id == 'foo'
