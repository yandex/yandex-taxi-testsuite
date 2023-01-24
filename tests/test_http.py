import aiohttp
from testsuite.utils import http


def test_make_response_basic():
    response = http.make_response()
    assert response.body is None
    assert response.status == 200

    response = http.make_response('foo')
    assert response.body == b'foo'
    assert response.status == 200

    response = http.make_response(b'foo')
    assert response.body == b'foo'
    assert response.status == 200

    response = http.make_response('error', status=500)
    assert response.body == b'error'
    assert response.status == 500


def test_make_response_json():
    response = http.make_response(json={'foo': 'bar'})
    assert response.body == b'{"foo": "bar"}'
    assert response.content_type == 'application/json'


async def test_multipart_form_data(mockserver):
    with aiohttp.MultipartWriter('form-data') as data:
        payload = aiohttp.payload.StringPayload('some_app_id')
        payload.set_content_disposition('form-data', name='application_id')
        data.append_payload(payload)

        payload = aiohttp.payload.BytesPayload(
            b'image_data',
            headers={'Content-Type': 'image/jpeg'},
        )
        payload.set_content_disposition('form-data', name='passport_photo')
        data.append_payload(payload)

        payload = aiohttp.payload.StringPayload('42')
        payload.set_content_disposition('form-data', name='page_number')
        data.append_payload(payload)

    headers = {
        'Content-Type': 'multipart/form-data; boundary=' + data.boundary,
    }

    @mockserver.handler('multipart/form-data')
    def mock(request):
        assert request.headers['content-type'].startswith(
            'multipart/form-data;',
        )

        form = request.form
        assert form['application_id'] == 'some_app_id'
        assert form['passport_photo'] == 'image_data'
        assert form['page_number'] == 42
        assert len(form) == 3

        return mockserver.make_response()

    async with aiohttp.ClientSession() as session:
        response = await session.post(
            mockserver.url('multipart/form-data'),
            headers=headers,
            data=data,
        )

    assert response.status == 200
    assert mock.times_called == 1
