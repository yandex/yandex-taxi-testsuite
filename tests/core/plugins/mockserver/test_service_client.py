import pytest


@pytest.mark.parametrize(
    'params, expected_query',
    [
        ({'key': 'value'}, b'key=value'),
        ({'key': 1}, b'key=1'),
        ({'key': 1.1}, b'key=1.1'),
        ({'key': ['v1', 'v2']}, b'key=v1&key=v2'),
        ({'key': ['str', 1, 2.2]}, b'key=str&key=1&key=2.2'),
        ([('key', 'str'), ('key', 1), ('key', 2.2)], b'key=str&key=1&key=2.2'),
    ],
)
async def test_query_params(
    mockserver,
    create_service_client,
    params,
    expected_query,
):
    @mockserver.json_handler('/arbitrary/path')
    async def _handler(request):
        assert request.query_string == expected_query
        return mockserver.make_response()

    client = create_service_client(mockserver.base_url)
    response = await client.post('arbitrary/path', params=params)
    assert response.status_code == 200


async def test_empty_http_header(mockserver, create_service_client):
    @mockserver.json_handler('/arbitrary/path')
    async def _handler(request):
        assert 'key-only-header' in request.headers
        assert not request.headers['key-only-header']

    client = create_service_client(mockserver.base_url)
    response = await client.post(
        'arbitrary/path',
        headers={'key-only-header': None},
    )
    assert response.status_code == 200


async def test_yarl_url(mockserver, create_service_client):
    @mockserver.json_handler('/arbitrary/../path')
    async def _handler(request):
        pass

    client = create_service_client(mockserver.base_url)
    response = await client.post(
        mockserver.url_encoded('arbitrary/../path'),
        headers={'key-only-header': None},
    )
    assert response.status_code == 200
