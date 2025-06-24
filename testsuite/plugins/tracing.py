import random
import uuid

import pytest

from testsuite.tracing import TraceidManager


@pytest.fixture(scope='session')
def testsuite_traceid_generator():
    """
    Fill free to override this fixture with our own.
    """

    def generator():
        return 'f' * 12 + ''.join(random.choices('0123456789abcdef', k=20))

    return generator


@pytest.fixture
def testsuite_trace_id(
    testsuite_traceid_generator, _testsuite_traceid_history
) -> str:
    """
    Testcase trace id.
    """
    trace_id = testsuite_traceid_generator()
    _testsuite_traceid_history.add(trace_id)
    return trace_id


@pytest.fixture
def testsuite_traceid_manager(
    testsuite_trace_id: str, _testsuite_traceid_history
) -> TraceidManager:
    """TraceidManager associated with current testcase.

    :returns: :py:class:`testsuite.tracing.TraceidManager`
    """
    return TraceidManager(testsuite_trace_id, _testsuite_traceid_history)


@pytest.fixture(scope='session')
def _testsuite_traceid_history():
    return set()
