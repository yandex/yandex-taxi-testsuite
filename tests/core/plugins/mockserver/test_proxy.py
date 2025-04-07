import asyncio

import pytest

from testsuite._internal import fixture_types


@pytest.fixture
def simple_client(mockserver_info):
    async def client(path: str):
        reader, writer = await asyncio.open_connection(
            mockserver_info.host, mockserver_info.port
        )

        request = f'GET {path} HTTP/1.0\r\n\r\n'
        writer.write(request.encode())
        await writer.drain()

        data = await reader.read()
        writer.close()
        await writer.wait_closed()

        lines = data.splitlines()
        assert len(lines) > 1
        assert lines[0].decode('utf-8') == ('HTTP/1.0 200 OK'), data

    return client


@pytest.mark.parametrize(
    'mock_url, request_path, expected_path',
    [
        ('/foo', '/foo/abc', '/foo/abc'),
        ('/foo', '/foo/abc?a=b', '/foo/abc'),
        ('/foo', '/foo/bar%20maurice?a=b', '/foo/bar maurice'),
        ('http://foo/', 'http://foo/abc', 'http://foo/abc'),
        ('http://foo/', 'http://foo/abc?a=b', 'http://foo/abc'),
        ('http://foo/', 'http://foo/bar%20maurice', 'http://foo/bar maurice'),
    ],
)
async def test_path_basic(
    mockserver: fixture_types.MockserverFixture,
    simple_client,
    mock_url,
    request_path,
    expected_path,
):
    @mockserver.aiohttp_json_handler(mock_url, prefix=True)
    def mock(request):
        pass

    await simple_client(request_path)
    mock_request = mock.next_call()['request']
    assert mock_request.original_path == expected_path
