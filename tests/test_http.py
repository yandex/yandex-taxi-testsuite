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
