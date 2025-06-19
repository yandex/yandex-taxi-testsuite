import pytest


@pytest.fixture(session='scope')
def testsuite_traceid_geneator():
    def gen():
        return 'foo'
    return gen


def test_override(traceid_manager):
    assert traceid_manager.trace_id == 'foo'
