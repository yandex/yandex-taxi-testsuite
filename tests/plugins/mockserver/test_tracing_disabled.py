# pylint: disable=protected-access
import aiohttp.test_utils
import pytest
import typing

from testsuite.mockserver import exceptions
from testsuite.mockserver import server


@pytest.fixture(autouse=True)
def disable_mockserver_tracing(mockserver):
    with mockserver.tracing(False):
        yield


async def test_mockserver_handles_request_from_other_test(
    mockserver,
    create_service_client,
):
    @mockserver.json_handler('/arbitrary/path')
    def _json_handler(request):
        return {'arbitrary_key': True}

    client = create_service_client(
        mockserver.base_url,
        headers={mockserver.trace_id_header: server.generate_trace_id()},
    )

    response = await client.post('arbitrary/path')
    assert response.status_code == 200
    assert response.json() == {'arbitrary_key': True}


@pytest.mark.parametrize(
    'http_headers',
    [
        {},  # no trace_id in http headers
        {server.DEFAULT_TRACE_ID_HEADER: ''},
        {server.DEFAULT_TRACE_ID_HEADER: 'id_without_testsuite-_prefix'},
    ],
)
async def test_mockserver_raises_on_unhandled_request_from_other_sources(
    http_headers,
    mockserver_info,
):
    mockserver = server.Server(
        mockserver_info,
        tracing_enabled=False,
    )
    errors = []
    with mockserver.new_session(asyncexc_append=errors.append) as session:
        request = _make_mocked_request(
            'POST',
            '/arbitrary/path',
            headers=http_headers,
        )
        await mockserver._handle_request(request)
        assert len(errors) == 1
        error = errors.pop()
        assert isinstance(error, exceptions.HandlerNotFoundError)


def _make_mocked_request(*args, **kwargs):
    request = aiohttp.test_utils.make_mocked_request(*args, **kwargs)
    request.original_path = request.path
    return request
