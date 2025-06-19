import uuid

import pytest

from testsuite.tracing import TraceidManager


@pytest.fixture(scope='session')
def testsuite_traceid_generator():
    """
    Fill free to override this fixture with our own.
    """

    def generator():
        return uuid.uuid4().hex

    return generator


@pytest.fixture
def testsuite_traceid_manager(
    testsuite_traceid_generator, _testsuite_traceid_history
) -> TraceidManager:
    """TraceidManager associated with current testcase.

    :returns: :py:class:`testsuite.tracing.TraceidManager`
    """
    trace_id = testsuite_traceid_generator()
    _testsuite_traceid_history.add(trace_id)
    return TraceidManager(trace_id, _testsuite_traceid_history)


@pytest.fixture(scope='session')
def _testsuite_traceid_history():
    return set()
