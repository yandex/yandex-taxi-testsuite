# pylint: disable=protected-access
import typing

import pytest

from testsuite.plugins import mockserver as mockserver_module
from testsuite.utils import net


@pytest.fixture(autouse=True)
def disable_mockserver_tracing(mockserver):
    with mockserver.tracing(False):
        yield


async def test_mockserver_handles_request_from_other_test(
        mockserver, create_service_client,
):
    @mockserver.json_handler('/arbitrary/path')
    def _json_handler(request):
        return {'arbitrary_key': True}

    client = create_service_client(
        mockserver.base_url,
        service_headers={
            mockserver.trace_id_header: mockserver_module._generate_trace_id(),
        },
    )

    response = await client.post('arbitrary/path')
    assert response.status_code == 200
    assert response.json() == {'arbitrary_key': True}


@pytest.mark.parametrize(
    'http_headers',
    [
        {},  # no trace_id in http headers
        {mockserver_module._DEFAULT_TRACE_ID_HEADER: ''},
        {
            mockserver_module._DEFAULT_TRACE_ID_HEADER: (
                'id_without_testsuite-_prefix'
            ),
        },
    ],
)
async def test_mockserver_raises_on_unhandled_request_from_other_sources(
        http_headers, create_service_client,
):
    class RequestStub(typing.NamedTuple):
        headers: dict
        path: str

    server = mockserver_module.Server(net.bind_socket(), tracing_enabled=False)
    context = server.new_session()
    context.__enter__()  # pylint: disable=no-member
    request = RequestStub(http_headers, '/arbitrary/path')
    with pytest.raises(mockserver_module.HandlerNotFoundError):
        await server._handle_request(request)
    # session.handle_failures
    with pytest.raises(mockserver_module.MockServerError):
        context.__exit__(None, None, None)  # pylint: disable=no-member
