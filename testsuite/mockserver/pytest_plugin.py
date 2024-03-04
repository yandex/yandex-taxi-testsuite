import contextlib
import typing
import warnings

import pytest

from testsuite import annotations
from testsuite.utils import colors

from . import classes
from . import exceptions
from . import server

MOCKSERVER_DEFAULT_PORT = 9999
MOCKSERVER_SSL_DEFAULT_PORT = 9998

_SSL_KEY_FILE_INI_KEY = 'mockserver-ssl-key-file'
_SSL_CERT_FILE_INI_KEY = 'mockserver-ssl-cert-file'

MOCKSERVER_PORT_HELP = """
{proto} mockserver port for default worker.
Random port is used by default. If testsuite is started with
--service-wait or --service-disabled default is forced to {default}.

NOTE: non-default workers always use random port.
"""


class MockserverPlugin:
    def __init__(self):
        self._invalidators = set()

    def pytest_runtest_call(self, item):
        for invalidator in self._invalidators:
            invalidator()

    @contextlib.contextmanager
    def register_invalidator(self, invalidator):
        self._invalidators.add(invalidator)
        try:
            yield
        finally:
            self._invalidators.discard(invalidator)


def pytest_addoption(parser):
    group = parser.getgroup('mockserver')
    group.addoption(
        '--mockserver-nofail',
        action='store_true',
        help='Do not fail if no handler is set.',
    )
    group.addoption(
        '--mockserver-host',
        default='localhost',
        help='Default host for http mockserver.',
    )
    group.addoption(
        '--mockserver-port',
        type=int,
        default=0,
        help=MOCKSERVER_PORT_HELP.format(
            proto='HTTP',
            default=MOCKSERVER_DEFAULT_PORT,
        ),
    )
    group.addoption(
        '--mockserver-ssl-host',
        default='localhost',
        help='Default host for https mockserver.',
    )
    group.addoption(
        '--mockserver-ssl-port',
        type=int,
        default=0,
        help=MOCKSERVER_PORT_HELP.format(
            proto='HTTPS',
            default=MOCKSERVER_SSL_DEFAULT_PORT,
        ),
    )
    group.addoption(
        '--mockserver-unix-socket',
        type=str,
        help='Bind server to unix socket instead of tcp',
    )
    group.addoption(
        '--mockserver-debug',
        action='store_true',
        help='Enable debugging logs.',
    )
    parser.addini(
        'mockserver-tracing-enabled',
        type='bool',
        default=False,
        help=(
            'When request trace-id header not from testsuite:\n'
            '  True: handle, if handler missing return http status 500\n'
            '  False: handle, if handler missing raise '
            'HandlerNotFoundError\n'
            'When request trace-id header from other test:\n'
            '  True: do not handle, return http status 500\n'
            '  False: handle, if handler missing raise HandlerNotFoundError'
        ),
    )
    parser.addini(
        'mockserver-trace-id-header',
        default=server.DEFAULT_TRACE_ID_HEADER,
        help=(
            'name of tracing http header, value changes from test to test and '
            'is constant within test'
        ),
    )
    parser.addini(
        'mockserver-span-id-header',
        default=server.DEFAULT_SPAN_ID_HEADER,
        help='name of tracing http header, value is unique for each request',
    )
    parser.addini(
        'mockserver-ssl-cert-file',
        type='pathlist',
        help='path to ssl certificate file to setup mockserver_ssl',
    )
    parser.addini(
        'mockserver-ssl-key-file',
        type='pathlist',
        help='path to ssl key file to setup mockserver_ssl',
    )
    parser.addini(
        'mockserver-http-proxy-enabled',
        type='bool',
        default=False,
        help='If enabled mockserver acts as http proxy',
    )


def pytest_configure(config):
    config.pluginmanager.register(MockserverPlugin(), 'mockserver_plugin')
    config.addinivalue_line(
        'markers',
        'mockserver_nosetup_errors: do not fail on mockserver setup errors',
    )


def pytest_register_object_hooks():
    return {
        '$mockserver': {'$fixture': '_mockserver_hook'},
        '$mockserver_https': {'$fixture': '_mockserver_https_hook'},
    }


@pytest.fixture(name='_mockserver_create_session')
def fixture_mockserver_create_session(
    _mockserver_trace_id: str,
    _mockserver_errors_clear,
):
    @contextlib.contextmanager
    def create_session(mockserver):
        with mockserver.new_session(_mockserver_trace_id) as session:
            with _mockserver_errors_clear(session):
                yield server.MockserverFixture(mockserver, session)

    return create_session


@pytest.fixture
def mockserver(
    _mockserver: server.Server,
    _mockserver_create_session,
) -> annotations.YieldFixture[server.MockserverFixture]:
    with _mockserver_create_session(_mockserver) as fixture:
        yield fixture


@pytest.fixture
async def mockserver_ssl(
    _mockserver_ssl: typing.Optional[server.Server],
    _mockserver_create_session,
) -> annotations.AsyncYieldFixture[server.MockserverSslFixture]:
    if _mockserver_ssl is None:
        raise exceptions.MockServerError(
            f'mockserver_ssl is not configured. {_SSL_KEY_FILE_INI_KEY} and '
            f'{_SSL_CERT_FILE_INI_KEY} must be specified in pytest.ini',
        )
    with _mockserver_create_session(_mockserver_ssl) as fixture:
        yield fixture


@pytest.fixture(scope='session')
def mockserver_info(_mockserver: server.Server) -> classes.MockserverInfo:
    """Returns mockserver information object."""
    return _mockserver.server_info


@pytest.fixture(scope='session')
def mockserver_ssl_info(
    _mockserver_ssl: typing.Optional[server.Server],
) -> typing.Optional[classes.MockserverInfo]:
    if _mockserver_ssl is None:
        return None
    return _mockserver_ssl.server_info


@pytest.fixture(scope='session')
def mockserver_ssl_cert(pytestconfig) -> typing.Optional[classes.SslCertInfo]:
    def _get_ini_path(name):
        values = pytestconfig.getini(name)
        if not values:
            return None
        if len(values) > 1:
            raise exceptions.MockServerError(
                f'{name} ini setting has multiple values',
            )
        return str(values[0])

    cert_path = _get_ini_path(_SSL_CERT_FILE_INI_KEY)
    key_path = _get_ini_path(_SSL_KEY_FILE_INI_KEY)
    if cert_path and key_path:
        return classes.SslCertInfo(
            cert_path=cert_path,
            private_key_path=key_path,
        )
    return None


@pytest.fixture(scope='session')
def _mockserver_getport(pytestconfig, worker_id):
    def getport(option_port, default_port):
        # Cannot use same port under xdist
        if worker_id != 'master':
            return 0
        # If service is started outside of testsuite use constant
        # port by default.
        if (
            pytestconfig.option.service_wait
            or pytestconfig.option.service_disable
        ):
            if option_port == 0:
                return default_port
        return option_port

    return getport


@pytest.fixture(scope='session')
async def _mockserver(
    pytestconfig,
    testsuite_logger,
    loop,
    _mockserver_getport,
) -> annotations.AsyncYieldFixture[server.Server]:
    if pytestconfig.option.mockserver_unix_socket:
        async with server.create_unix_server(
            socket_path=pytestconfig.option.mockserver_unix_socket,
            loop=loop,
            testsuite_logger=testsuite_logger,
            pytestconfig=pytestconfig,
        ) as result:
            yield result
    else:
        port = _mockserver_getport(
            pytestconfig.option.mockserver_port,
            MOCKSERVER_DEFAULT_PORT,
        )
        async with server.create_server(
            host=pytestconfig.option.mockserver_host,
            port=port,
            loop=loop,
            testsuite_logger=testsuite_logger,
            pytestconfig=pytestconfig,
            ssl_info=None,
        ) as result:
            yield result


@pytest.fixture(scope='session')
async def _mockserver_ssl(
    pytestconfig,
    testsuite_logger,
    loop,
    mockserver_ssl_cert,
    _mockserver_getport,
) -> annotations.AsyncYieldFixture[typing.Optional[server.Server]]:
    if mockserver_ssl_cert:
        port = _mockserver_getport(
            pytestconfig.option.mockserver_ssl_port,
            MOCKSERVER_SSL_DEFAULT_PORT,
        )
        async with server.create_server(
            host=pytestconfig.option.mockserver_ssl_host,
            port=port,
            loop=loop,
            testsuite_logger=testsuite_logger,
            pytestconfig=pytestconfig,
            ssl_info=mockserver_ssl_cert,
        ) as result:
            yield result
    else:
        yield None


@pytest.fixture
def _mockserver_trace_id() -> str:
    return server.generate_trace_id()


@pytest.fixture(scope='session')
def _mockserver_hook(mockserver_info):
    def wrapper(doc: dict):
        return _mockserver_info_hook(doc, '$mockserver', mockserver_info)

    return wrapper


@pytest.fixture(scope='session')
def _mockserver_https_hook(mockserver_ssl_info):
    def wrapper(doc: dict):
        return _mockserver_info_hook(
            doc,
            '$mockserver_https',
            mockserver_ssl_info,
        )

    return wrapper


@pytest.fixture(name='_mockserver_errors_clear')
def fixture_mockserver_errors_clear(
    _mockserver_plugin: MockserverPlugin,
    request,
    mockserver_nosetup_errors,
):
    """
    Clear mockserver errors at startup.

    Required for backward compatibility with older testsuite versions.
    """
    marker = request.node.get_closest_marker('mockserver_nosetup_errors')
    if marker:
        warnings.warn(
            'pytest.mark.mockserver_nosetup_errors is for backward '
            'compatibility only, please rewrite your code',
            DeprecationWarning,
        )
        mockserver_nosetup_errors = True

    @contextlib.contextmanager
    def errors_clear(session: server.Session):
        if not mockserver_nosetup_errors:
            yield
            return
        with _mockserver_plugin.register_invalidator(session.clear_errors):
            yield

    return errors_clear


@pytest.fixture(name='mockserver_nosetup_errors', scope='session')
def fixture_mockserver_nosetup_errors():
    return False


@pytest.fixture(name='_mockserver_plugin', scope='session')
def fixture_mockserver_plugin(pytestconfig) -> MockserverPlugin:
    return pytestconfig.pluginmanager.get_plugin('mockserver_plugin')


def _mockserver_info_hook(doc: dict, key=None, mockserver_info=None):
    if mockserver_info is None:
        raise RuntimeError(f'Missing {key} argument')
    if not doc.get('$schema', True):
        schema = ''
    elif mockserver_info.ssl is not None:
        schema = 'https://'
    else:
        schema = 'http://'
    return '%s%s:%d%s' % (
        schema,
        mockserver_info.host,
        mockserver_info.port,
        doc[key],
    )
