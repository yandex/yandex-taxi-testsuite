import pytest


@pytest.fixture
def mockserver_errors_pop(_asyncexc):
    def pop():
        return _asyncexc.pop()

    return pop


@pytest.fixture
def mockserver_errors_list(_asyncexc):
    return _asyncexc
