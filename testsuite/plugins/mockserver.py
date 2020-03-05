import contextlib
import datetime
import logging
import ssl
import sys
import time
import traceback
import typing
import uuid

import aiohttp.web
import pytest

from testsuite.utils import callinfo
from testsuite.utils import http
from testsuite.utils import net as net_utils
from testsuite.utils import url_util

_SSL_KEY_FILE_INI_KEY = 'mockserver-ssl-key-file'
_SSL_CERT_FILE_INI_KEY = 'mockserver-ssl-cert-file'

REQUEST_FROM_ANOTHER_TEST_ERROR = 'Internal error: request is from other test'

_DEFAULT_TRACE_ID_HEADER = 'X-YaTraceId'
_DEFAULT_SPAN_ID_HEADER = 'X-YaSpanId'

_TRACE_ID_PREFIX = 'testsuite-'

_MISSING_HANDLER_ERROR = (
    'perhaps you forget to setup mockserver handler, use --mockserver-nofail '
    'to suppress these errors{}'
)
_SUPPORTED_ERRORS_HEADER = 'X-Testsuite-Supported-Errors'
_ERROR_HEADER = 'X-Testsuite-Error'

_LOGGER_HEADERS = (
    ('X-YaTraceId', 'trace_id'),
    ('X-YaSpanId', 'span_id'),
    ('X-YaRequestId', 'link'),
)

logger = logging.getLogger(__name__)


class BaseError(Exception):
    """Base class for exceptions from this module."""


class MockServerError(BaseError):
    pass


class HandlerNotFoundError(MockServerError):
    def __init__(self, tracing_enabled):
        self.tracing_enabled = tracing_enabled
        super().__init__()


class SslInfo(typing.NamedTuple):
    cert_path: str
    private_key_path: str


class MockserverInfo(typing.NamedTuple):
    host: str
    port: int
    base_url: str
    ssl: typing.Optional[SslInfo]

    def url(self, path: str) -> str:
        """Concats ``base_url`` and provided ``path``."""
        return url_util.join(self.base_url, path)


class Handler:
    def __init__(self, func, *, raw_request=False, json_response=False):
        self.orig_func = func
        self.callqueue = callinfo.acallqueue(func)
        self.raw_request = raw_request
        self.json_response = json_response

    def __repr__(self):
        return (
            f'mockserver.Handler({self.orig_func!r}, '
            f'raw_request={self.raw_request}, '
            f'json_response={self.json_response})'
        )

    async def __call__(self, request):
        if not self.raw_request:
            request = await http.wrap_request(request)
        response = await self.callqueue(request)
        if not self.json_response:
            return response
        if isinstance(response, aiohttp.web.Response):
            return response
        return http.make_response(json=response)


class Session:
    def __init__(self, reporter=None, tracing_enabled=True, trace_id=None):
        if trace_id is None:
            trace_id = _generate_trace_id()
        self.trace_id = trace_id
        self.reporter = reporter
        self.tracing_enabled = tracing_enabled
        self.handlers = {}
        self.failures = []
        self.prefix_handlers = {}

    def add_failure(self, request, error):
        self.failures.append((request, error))

    def get_handler(self, path):
        if path in self.handlers:
            return self.handlers[path]
        for prefix in self.prefix_handlers:
            if path.startswith(prefix):
                return self.prefix_handlers[prefix]
        raise HandlerNotFoundError(self.tracing_enabled)

    async def handle_request(self, request):
        try:
            handler = self.get_handler(request.path)
            response = await handler(request)
            if isinstance(response, aiohttp.web.Response):
                return response
            raise MockServerError(
                'aiohttp.web.Response instance is expected '
                f'{response!r} given',
            )
        except HandlerNotFoundError:
            raise
        except http.MockedError as exc:
            return _mocked_error_response(request, exc.error_code)
        except Exception as exc:
            exc_info = sys.exc_info()
            self.add_failure(request, exc)
            self._report_handler_failure(request, exc_info, handler)
            raise

    def _report_handler_failure(self, request, exc_info, handler):
        if self.reporter:
            self.reporter.write_line('Mockserver handler failed.', red=True)
            self.reporter.write_line('')
            self.reporter.write_line(
                f'{handler} crashed while responding to {request.url}',
                red=True,
            )
            self.reporter.write_line('')
            for line in traceback.format_exception(*exc_info):
                self.reporter.write(line, red=True)

    def register_handler(self, path, func, prefix=False):
        path = url_util.ensure_leading_separator(path)
        if prefix:
            handlers = self.prefix_handlers
        else:
            handlers = self.handlers
        handlers[path] = func
        return func

    def handle_failures(self, message):
        if not self.failures:
            return
        failures, self.failures = self.failures, []
        failure_messages = set()
        cause = None
        for request, failure in failures:
            if isinstance(failure, HandlerNotFoundError):
                text = _MISSING_HANDLER_ERROR.format(
                    ' (tracing enabled)' if failure.tracing_enabled else '',
                )
            else:
                text = repr(failure)
            if cause is None:
                cause = failure
            failure_messages.add(f' * {request.path}: {text}')
        messages = [message, *sorted(failure_messages)]
        raise MockServerError('\n'.join(messages)) from cause


class HandlerInstaller:
    """Mockserver handler installer."""

    def __init__(self, server, session):
        self._server = server
        self._session = session

    @property
    def base_url(self) -> str:
        """Mockserver base url."""
        return self._server.server_info.base_url

    @property
    def host(self) -> str:
        """Mockserver hostname."""
        return self._server.server_info.host

    @property
    def port(self) -> int:
        """Mockserver port."""
        return self._server.server_info.port

    @property
    def trace_id_header(self) -> str:
        return self._server.trace_id_header

    @property
    def span_id_header(self) -> str:
        return self._server.span_id_header

    @property
    def trace_id(self) -> str:
        return self._session.trace_id

    def handler(
            self, path, prefix=False, raw_request=False, json_response=False,
    ):
        """Register basic http handler for ``path``.

        Returns decorator that registers handler ``path``. Original function is
        wrapped with :ref:`AsyncCallQueue`.

        :param path: match url by prefix if ``True`` exact match otherwise
        :param raw_request: pass ``aiohttp.web.Response`` to handler instead of
            ``testsuite.utils.http.Request``

        .. code-block:: python

           @mockserver.handler('/service/path')
           def handler(request: testsuite.utils.http.Request):
               return mockserver.make_response('Hello, world!')
        """

        def decorator(func):
            handler = Handler(
                func, raw_request=raw_request, json_response=json_response,
            )
            self._session.register_handler(path, handler, prefix=prefix)
            return handler.callqueue

        return decorator

    def json_handler(self, path, prefix=False, raw_request=False):
        """Register json http handler for ``path``.

        Returns decorator that registers handler ``path``. Original function is
        wrapped with :ref:`AsyncCallQueue`.

        :param path: match url by prefix if ``True`` exact match otherwise
        :param raw_request: pass ``aiohttp.web.Response`` to handler instead of
            ``testsuite.utils.http.Request``

        .. code-block:: python

           @mockserver.json_handler('/service/path')
           def handler(request: testsuite.utils.http.Request):
               # Return JSON document
               return {...}
               # or call to mockserver.make_response()
               return mockserver.make_response(...)
        """
        return self.handler(
            path, prefix=prefix, raw_request=raw_request, json_response=True,
        )

    def url(self, path):
        """Builds mockserver url for ``path``"""
        return url_util.join(self.base_url, path)

    def ignore_trace_id(self):
        return self.tracing(False)

    @contextlib.contextmanager
    def tracing(self, value: bool = True):
        original_value = self._session.tracing_enabled
        try:
            self._session.tracing_enabled = value
            yield
        finally:
            self._session.tracing_enabled = original_value

    def get_callqueue_for(self, path):
        return self._session.get_handler(path).callqueue

    make_response = staticmethod(http.make_response)

    TimeoutError = http.TimeoutError
    NetworkError = http.NetworkError


# pylint: disable=too-many-instance-attributes
class Server:
    session = None

    def __init__(
            self,
            mockserver_info: MockserverInfo,
            *,
            logger=None,
            nofail=False,
            reporter=None,
            tracing_enabled=True,
            trace_id_header=_DEFAULT_TRACE_ID_HEADER,
            span_id_header=_DEFAULT_SPAN_ID_HEADER,
    ):
        self._info = mockserver_info
        self._logger = logger
        self._nofail = nofail
        self._reporter = reporter
        self._tracing_enabled = tracing_enabled
        self._trace_id_header = trace_id_header
        self._span_id_header = span_id_header

    @property
    def tracing_enabled(self) -> bool:
        if self.session is None:
            return self._tracing_enabled
        return self.session.tracing_enabled

    @property
    def trace_id_header(self):
        return self._trace_id_header

    @property
    def span_id_header(self):
        return self._span_id_header

    @property
    def server_info(self) -> MockserverInfo:
        return self._info

    @contextlib.contextmanager
    def new_session(self, trace_id=None):
        self.session = Session(self._reporter, self._tracing_enabled, trace_id)
        try:
            yield self.session
        finally:
            session = self.session
            self.session = None
            session.handle_failures('Mockserver failure')

    async def handle_request(self, request):
        if not self._logger:
            return await self._handle_request(request)

        started = time.perf_counter()
        fields = {
            '_type': 'mockserver_request',
            'timestamp': datetime.datetime.utcnow(),
            'level': 'INFO',
            'method': request.method,
            'url': request.url,
        }
        for header, key in _LOGGER_HEADERS:
            if header in request.headers:
                fields[key] = request.headers[header]
        try:
            response = await self._handle_request(request)
            fields['meta_code'] = response.status
            fields['status'] = 'DONE'
            return response
        except BaseException as exc:
            fields['level'] = 'ERROR'
            fields['status'] = 'FAIL'
            fields['exc_info'] = str(exc)
            raise
        finally:
            delay_ms = 1000 * (time.perf_counter() - started)
            fields['delay'] = f'{delay_ms:.3f}ms'
            self._logger.log_entry(fields)

    async def _handle_request(self, request):
        trace_id = request.headers.get(self.trace_id_header)
        nofail = (
            self._nofail
            or self.tracing_enabled
            and not _is_from_client_fixture(trace_id)
        )
        if not self.session:
            error_message = 'Internal error: missing mockserver fixture'
            if nofail:
                return _internal_error(error_message)
            raise MockServerError(error_message)

        if self.tracing_enabled and _is_other_test(
                trace_id, self.session.trace_id,
        ):
            self._report_other_test_request(request, trace_id)
            return _internal_error(REQUEST_FROM_ANOTHER_TEST_ERROR)
        try:
            return await self.session.handle_request(request)
        except HandlerNotFoundError as exc:
            if nofail:
                self._report_handler_not_found(request, level=logging.WARNING)
                return _internal_error(
                    'Internal error: mockserver handler not found',
                )
            self._report_handler_not_found(request)
            self.session.add_failure(request, exc)
            raise

    def _report_handler_not_found(self, request, level=logging.ERROR):
        logger.log(
            level,
            'Mockserver handler not installed for path %s',
            request.path,
        )

    def _report_other_test_request(self, request, trace_id):
        logger.warning(
            'Mockserver called path %s with previous test trace_id %s',
            request.path,
            trace_id,
        )


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
        help=(
            'Http mockserver port for default (master) worker. Set 0 to use '
            'random port. NOTE: non-default workers always use random port.'
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
        help=(
            'Https mockserver port for default (master) worker. Set 0 to use '
            'random port. NOTE: non-default workers always use random port.'
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
        default=_DEFAULT_TRACE_ID_HEADER,
        help=(
            'name of tracing http header, value changes from test to test and '
            'is constant within test'
        ),
    )
    parser.addini(
        'mockserver-span-id-header',
        default=_DEFAULT_SPAN_ID_HEADER,
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


@pytest.fixture
async def mockserver(_mockserver, _mockserver_trace_id):
    with _mockserver.new_session(_mockserver_trace_id) as session:
        yield HandlerInstaller(_mockserver, session)


@pytest.fixture
def _mockserver_trace_id():
    return _generate_trace_id()


@pytest.fixture
async def mockserver_ssl(_mockserver_ssl, _mockserver_trace_id):
    if _mockserver_ssl is None:
        raise MockServerError(
            f'mockserver_ssl is not configured. {_SSL_KEY_FILE_INI_KEY} and '
            f'{_SSL_CERT_FILE_INI_KEY} must be specified in pytest.ini',
        )
    with _mockserver_ssl.new_session(_mockserver_trace_id) as session:
        yield HandlerInstaller(_mockserver_ssl, session)


@pytest.fixture(scope='session')
def mockserver_info(_mockserver: Server) -> MockserverInfo:
    """Returns mockserver information object."""
    return _mockserver.server_info


@pytest.fixture(scope='session')
def mockserver_ssl_info(_mockserver_ssl):
    if _mockserver_ssl is None:
        return None
    return _mockserver_ssl.server_info


@pytest.fixture(scope='session')
async def _mockserver(pytestconfig, worker_id, testsuite_logger, loop):
    async with _mockserver_context(
            pytestconfig.option.mockserver_host,
            pytestconfig.option.mockserver_port,
            worker_id,
            loop,
            testsuite_logger,
            pytestconfig,
            ssl_info=None,
    ) as server:
        yield server


@pytest.fixture(scope='session')
async def _mockserver_ssl(pytestconfig, worker_id, testsuite_logger, loop):
    def _get_ini_path(name):
        values = pytestconfig.getini(name)
        if not values:
            return None
        if len(values) > 1:
            raise MockServerError(f'{name} ini setting has multiple values')
        return str(values[0])

    cert_path = _get_ini_path(_SSL_CERT_FILE_INI_KEY)
    key_path = _get_ini_path(_SSL_KEY_FILE_INI_KEY)

    if cert_path and key_path:
        ssl_info = SslInfo(cert_path=cert_path, private_key_path=key_path)
        async with _mockserver_context(
                pytestconfig.option.mockserver_ssl_host,
                pytestconfig.option.mockserver_ssl_port,
                worker_id,
                loop,
                testsuite_logger,
                pytestconfig,
                ssl_info,
        ) as server:
            yield server
    else:
        yield None


@contextlib.asynccontextmanager
async def _mockserver_context(
        host, port, worker_id, loop, testsuite_logger, pytestconfig, ssl_info,
):
    port = port if worker_id == 'master' else 0
    sock = net_utils.bind_socket(host, port)
    mockserver_info = _create_mockserver_info(sock, host, ssl_info)
    with contextlib.closing(sock):
        server = Server(
            mockserver_info,
            logger=testsuite_logger,
            nofail=pytestconfig.option.mockserver_nofail,
            reporter=pytestconfig.pluginmanager.get_plugin('terminalreporter'),
            tracing_enabled=pytestconfig.getini('mockserver-tracing-enabled'),
            trace_id_header=pytestconfig.getini('mockserver-trace-id-header'),
            span_id_header=pytestconfig.getini('mockserver-span-id-header'),
        )
        ssl_context = _create_ssl_context(ssl_info)
        web_server = aiohttp.web.Server(server.handle_request, loop=loop)
        loop_server = await loop.create_server(
            web_server, sock=sock, ssl=ssl_context,
        )
        try:
            yield server
        finally:
            loop_server.close()
            await loop_server.wait_closed()


def _create_mockserver_info(
        sock, host: str, ssl_info: typing.Optional[SslInfo],
):
    sock_address = sock.getsockname()
    schema = 'https' if ssl_info else 'http'
    port = sock_address[1]
    base_url = '%s://%s:%d/' % (schema, host, port)
    return MockserverInfo(
        host=host, port=port, base_url=base_url, ssl=ssl_info,
    )


def _create_ssl_context(ssl_info: typing.Optional[SslInfo]):
    if not ssl_info:
        return None
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(ssl_info.cert_path, ssl_info.private_key_path)
    return ssl_context


def _internal_error(message='Internal error'):
    return http.make_response(message, status=500)


def _mocked_error_response(request, error_code):
    if _SUPPORTED_ERRORS_HEADER not in request.headers:
        raise MockServerError(
            'Service does not support mockserver errors protocol',
        )
    supported_errors = request.headers[_SUPPORTED_ERRORS_HEADER].split(',')
    if error_code not in supported_errors:
        raise MockServerError(
            f'Service does not support mockserver error of type {error_code}',
        )
    return http.make_response(
        response='', status=599, headers={_ERROR_HEADER: error_code},
    )


def _generate_trace_id():
    return _TRACE_ID_PREFIX + uuid.uuid4().hex


def _is_from_client_fixture(trace_id: str):
    return trace_id is not None and trace_id.startswith(_TRACE_ID_PREFIX)


def _is_other_test(trace_id: str, current_trace_id: str):
    return trace_id != current_trace_id and _is_from_client_fixture(trace_id)
