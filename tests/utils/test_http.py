import pytest

from testsuite.utils import http


def test_response_is_immutable():
    response = http.Response(text='hello there')

    with pytest.raises(AttributeError) as err:
        response.body = 'hello'.encode('utf-8')
        response.text = 'some other text'
        response.status = 404
        response.content_type = 'application/json'
        response.charset = 'utf-8'

    assert err.value
