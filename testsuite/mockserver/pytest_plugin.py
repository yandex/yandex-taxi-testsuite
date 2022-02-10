import typing

import pytest

from testsuite import annotations
from testsuite.utils import colors

from . import classes
from . import exceptions
from . import reporter_plugin
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
            proto='HTTP', default=MOCKSERVER_DEFAULT_PORT,
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
            proto='HTTPS', default=MOCKSERVER_SSL_DEFAULT_PORT,
        ),
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
    config.pluginmanager.register(
        reporter_plugin.MockserverReporterPlugin(
            colors_enabled=colors.should_enable_color(config),
        ),
        'mockserver_reporter',
    )


def pytest_register_object_hooks():
    return {
        '$mockserver': {'$fixture': '_mockserver_hook'},
        '$mockserver_https': {'$fixture': '_mockserver_https_hook'},
    }


@pytest.fixture
def mockserver(
        _mockserver: server.Server, _mockserver_trace_id: str,
) -> annotations.YieldFixture[server.MockserverFixture]:
    with _mockserver.new_session(_mockserver_trace_id) as session:
        yield server.MockserverFixture(_mockserver, session)


@pytest.fixture
async def mockserver_ssl(
        _mockserver_ssl: typing.Optional[server.Server],
        _mockserver_trace_id: str,
) -> annotations.AsyncYieldFixture[server.MockserverSslFixture]:
    if _mockserver_ssl is None:
        raise exceptions.MockServerError(
            f'mockserver_ssl is not configured. {_SSL_KEY_FILE_INI_KEY} and '
            f'{_SSL_CERT_FILE_INI_KEY} must be specified in pytest.ini',
        )
    with _mockserver_ssl.new_session(_mockserver_trace_id) as session:
        yield server.MockserverFixture(_mockserver_ssl, session)


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
            cert_path=cert_path, private_key_path=key_path,
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
        _mockserver_reporter,
        _mockserver_getport,
) -> annotations.AsyncYieldFixture[server.Server]:
    port = _mockserver_getport(
        pytestconfig.option.mockserver_port, MOCKSERVER_DEFAULT_PORT,
    )
    async with server.create_server(
            pytestconfig.option.mockserver_host,
            port,
            loop,
            testsuite_logger,
            _mockserver_reporter,
            pytestconfig,
            ssl_info=None,
    ) as result:
        yield result


@pytest.fixture(scope='session')
async def _mockserver_ssl(
        pytestconfig,
        testsuite_logger,
        loop,
        mockserver_ssl_cert,
        _mockserver_reporter,
        _mockserver_getport,
) -> annotations.AsyncYieldFixture[typing.Optional[server.Server]]:
    if mockserver_ssl_cert:
        port = _mockserver_getport(
            pytestconfig.option.mockserver_ssl_port,
            MOCKSERVER_SSL_DEFAULT_PORT,
        )
        async with server.create_server(
                pytestconfig.option.mockserver_ssl_host,
                port,
                loop,
                testsuite_logger,
                _mockserver_reporter,
                pytestconfig,
                mockserver_ssl_cert,
        ) as result:
            yield result
    else:
        yield None


@pytest.fixture(scope='session')
def _mockserver_reporter(
        pytestconfig,
) -> reporter_plugin.MockserverReporterPlugin:
    return pytestconfig.pluginmanager.get_plugin('mockserver_reporter')


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
            doc, '$mockserver_https', mockserver_ssl_info,
        )

    return wrapper


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
