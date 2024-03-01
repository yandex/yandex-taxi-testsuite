import pytest

from testsuite.mockserver import exceptions


@pytest.fixture
async def inject_setup_error(mockserver_client, mockserver):
    response = await mockserver_client.get('/inject/error')
    assert response.status_code == 500


def test_setup_errors_basic(inject_setup_error, mockserver):
    assert len(mockserver._session._errors) == 1
    error = mockserver._session._errors.pop()
    assert isinstance(error, exceptions.HandlerNotFoundError)


@pytest.mark.mockserver_nosetup_errors
def test_setup_errors_basic(inject_setup_error, mockserver):
    pass


@pytest.fixture
def mockserver_nosetup_errors():
    return False
