# pylint: disable=protected-access
import pytest

from testsuite.mockserver import classes
from testsuite.mockserver import exceptions
from testsuite.mockserver import server


def test_session():
    session = server.Session()

    def handler(request):
        pass

    handler = session.register_handler('/foo', handler)
    found_handler, _ = session.get_handler('/foo')
    assert found_handler is handler

    def handler2(request):
        pass

    handler2 = session.register_handler('/foo', handler2)
    found_handler_2, _ = session.get_handler('/foo')
    assert found_handler_2 is handler2

    with pytest.raises(exceptions.HandlerNotFoundError):
        session.get_handler('/bar')


def test_installer_base_url():
    session = server.Session()
    dummy_server = _create_server()
    installer = server.MockserverFixture(dummy_server, session)
    assert installer.base_url == dummy_server.server_info.base_url


async def test_installer_handlers():
    session = server.Session()
    dummy_server = _create_server()
    installer = server.MockserverFixture(dummy_server, session)

    @installer.handler('/foo')
    def handler1(request):
        return 'result'

    @installer.json_handler('/bar')
    def handler2(request):
        return {}

    foo_handler, _ = session.get_handler('/foo')
    assert foo_handler.callqueue is handler1
    bar_handler, _ = session.get_handler('/bar')
    assert bar_handler.callqueue is handler2


@pytest.mark.parametrize(
    ('base_prefix', 'prefix', 'http_proxy_enabled', 'expected'),
    [
        ('', 'foo', False, '/foo'),
        ('', '/foo', False, '/foo'),
        ('', 'foo', True, '/foo'),
        ('', '/foo', True, '/foo'),
        ('', 'http://foo/', True, 'http://foo/'),
        ('http://foo/', 'bar', True, 'http://foo/bar'),
        ('http://foo/', '/bar', True, 'http://foo/bar'),
    ],
)
def test_mockserver_new(base_prefix, prefix, http_proxy_enabled, expected):
    session = server.Session()
    dummy_server = _create_server(http_proxy_enabled=http_proxy_enabled)
    installer = server.MockserverFixture(
        dummy_server, session, base_prefix=base_prefix,
    )
    installer = installer.new(prefix)
    assert installer._base_prefix == expected


def _create_server(**kwargs):
    mockserver_info = classes.MockserverInfo(
        host='', port=0, base_url='http://mockserver/', ssl=None,
    )
    return server.Server(mockserver_info, **kwargs)
