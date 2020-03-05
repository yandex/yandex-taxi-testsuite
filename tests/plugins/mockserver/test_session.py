import pytest

from testsuite.plugins import mockserver


class DummyServer:
    @property
    def server_info(self):
        return mockserver.MockserverInfo(
            host='', port='', base_url='http://mockserver/', ssl=None,
        )


def test_session():
    session = mockserver.Session()

    def handler(request):
        pass

    handler = session.register_handler('/foo', handler)
    assert session.get_handler('/foo') is handler

    def handler2(request):
        pass

    handler2 = session.register_handler('/foo', handler2)
    assert session.get_handler('/foo') is handler2

    with pytest.raises(mockserver.HandlerNotFoundError):
        session.get_handler('/bar')


def test_installer_base_url():
    session = mockserver.Session()
    server = DummyServer()
    installer = mockserver.HandlerInstaller(server, session)
    assert installer.base_url == server.server_info.base_url


def test_installer_handlers():
    session = mockserver.Session()
    installer = mockserver.HandlerInstaller(DummyServer(), session)

    @installer.handler('/foo')
    def handler1(request):
        return 'result'

    @installer.json_handler('/bar')
    def handler2(request):
        return {}

    assert session.get_handler('/foo').callqueue is handler1
    assert session.get_handler('/bar').callqueue is handler2
