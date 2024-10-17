import pytest

from testsuite.utils import http


@pytest.mark.parametrize('chunked', [None, True])
async def test_mockserver_raises_on_get_with_content(
    mockserver,
    mockserver_client,
    mockserver_errors_pop,
    chunked: bool,
):
    @mockserver.handler('/foo')
    def _foo_handler(request):
        return mockserver.make_response(status=200)

    response = await mockserver_client.get(
        '/foo',
        data='some text',
        chunked=chunked,
    )
    assert response.status_code == 500

    error = mockserver_errors_pop()
    assert isinstance(error, http.InvalidRequestError)
