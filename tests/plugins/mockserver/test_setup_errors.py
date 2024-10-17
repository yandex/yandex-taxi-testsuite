import pytest

from testsuite.mockserver import exceptions


@pytest.fixture
async def inject_setup_error(mockserver_client, mockserver):
    response = await mockserver_client.get('/inject/error')
    assert response.status_code == 500


def test_setup_errors_basic(
    inject_setup_error,
    mockserver_errors_pop,
    mockserver_errors_list,
):
    assert len(mockserver_errors_list) == 1
    error = mockserver_errors_pop()
    assert isinstance(error, exceptions.HandlerNotFoundError)
