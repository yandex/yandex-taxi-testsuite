import pytest
import uuid

from testsuite.tracing import TraceidManager

_TRACE_ID_PREFIX = 'testsuite-'


@pytest.fixture(scope='session')
def testsuite_traceid_generator():
    """
    Fill free to override this fixture with our own.
    """
    return _TRACE_ID_PREFIX + uuid.uuid4().hex


@pytest.fixture
def testsuite_traceid_manager(testsuite_traceid_generator, _testsuite_traceid_history):
    trace_id = testsuite_traceid_generator()
    _testsuite_traceid_history.add(trace_id)
    return TraceidManager(trace_id, _testsuite_traceid_history)


@pytest.fixture(scope='session')
def _testsuite_traceid_history():
    return []
