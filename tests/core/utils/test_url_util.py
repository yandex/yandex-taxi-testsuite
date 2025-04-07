import pytest

from testsuite.utils import url_util


@pytest.mark.parametrize(
    'url,expected',
    [
        ('http://localhost:9999/', 'http://localhost:9999/'),
        ('http://localhost:9999', 'http://localhost:9999/'),
    ],
)
def test_ensure_trailing_separator(url, expected):
    assert url_util.ensure_trailing_separator(url) == expected


@pytest.mark.parametrize(
    'base,path,expected',
    [
        ('http://localhost:9999', 'foo', 'http://localhost:9999/foo'),
        ('http://localhost:9999', '/foo', 'http://localhost:9999/foo'),
        ('http://localhost:9999/', 'foo', 'http://localhost:9999/foo'),
        ('http://localhost:9999/', '/foo', 'http://localhost:9999/foo'),
        ('http://localhost:9999/', '//foo', 'http://localhost:9999//foo'),
        ('http://localhost:9999', '//foo', 'http://localhost:9999//foo'),
        ('http://localhost:9999//', 'foo', 'http://localhost:9999//foo'),
    ],
)
def test_join(base, path, expected):
    assert url_util.join(base, path) == expected


@pytest.mark.parametrize('path,expected', [('/foo', '/foo'), ('bar', '/bar')])
def test_ensure_leading_separator(path, expected):
    assert url_util.ensure_leading_separator(path) == expected
