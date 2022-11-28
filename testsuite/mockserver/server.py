import contextlib
import datetime
import itertools
import logging
import re
import ssl
import time
import typing
import uuid
import warnings

import aiohttp.web

from testsuite.utils import callinfo
from testsuite.utils import compat
from testsuite.utils import http
from testsuite.utils import net as net_utils
from testsuite.utils import url_util

from . import classes
from . import exceptions
from . import magicargs
from . import reporter_plugin

DEFAULT_TRACE_ID_HEADER = 'X-YaTraceId'
DEFAULT_SPAN_ID_HEADER = 'X-YaSpanId'

_TRACE_ID_PREFIX = 'testsuite-'

REQUEST_FROM_ANOTHER_TEST_ERROR = 'Internal error: request is from other test'

_SUPPORTED_ERRORS_HEADER = 'X-Testsuite-Supported-Errors'
_ERROR_HEADER = 'X-Testsuite-Error'

_LOGGER_HEADERS = (
    ('X-YaTraceId', 'trace_id'),
    ('X-YaSpanId', 'span_id'),
    ('X-YaRequestId', 'link'),
)

logger = logging.getLogger(__name__)

RouteParams = typing.Dict[str, str]


class Handler:
    def __init__(self, func, *, raw_request=False, json_response=False):
        self.callqueue = callinfo.acallqueue(func)
        self.handler_args = magicargs.MagicArgsHandler(
            func, raw_request=raw_request,
        )
        self.json_response = json_response
        self.orig_func = func

    def __repr__(self):
        return (
            f'{Handler.__module__}.{Handler.__name__}({self.orig_func!r}, '
            f'raw_request={self.handler_args.raw_request}, '
            f'json_response={self.json_response})'
        )

    async def __call__(self, request: aiohttp.web.BaseRequest, **kwargs):
        args, kwargs = await self.handler_args.build_args(request, kwargs)
        response = await self.callqueue(*args, **kwargs)
        if not self.json_response:
            return response
        if isinstance(response, aiohttp.web.Response):
            return response
        return http.make_response(json=response)


class Session:
    handlers: typing.Dict[str, Handler]
    prefix_handlers: typing.List[typing.Tuple[str, Handler]]
    regex_handlers: typing.List[typing.Tuple[typing.Pattern, Handler]]

    def __init__(
            self,
            reporter: typing.Optional[
                reporter_plugin.MockserverReporterPlugin
            ] = None,
            *,
            tracing_enabled=True,
            trace_id=None,
            http_proxy_enabled=False,
            mockserver_host=None,
    ):
        if trace_id is None:
            trace_id = generate_trace_id()
        self.trace_id = trace_id
        self.reporter = reporter
        self.tracing_enabled = tracing_enabled
        self.handlers = {}
        self.prefix_handlers = []
        self.regex_handlers = []
        self.http_proxy_enabled = http_proxy_enabled
        self.mockserver_host = mockserver_host

    def get_handler(self, path: str) -> typing.Tuple[Handler, RouteParams]:
        handler = self.handlers.get(path)
        if handler is not None:
            return handler, {}
        for pattern, handler in reversed(self.regex_handlers):
            match = pattern.fullmatch(path)
            if match:
                return handler, match.groupdict()
        for prefix, handler in reversed(self.prefix_handlers):
            if path.startswith(prefix):
                return handler, {}
        raise exceptions.HandlerNotFoundError(
            self._get_handler_not_found_message(path),
        )

    def _get_handler_not_found_message(self, path: str) -> str:
        if self.tracing_enabled:
            tracing_state = 'enabled'
        else:
            tracing_state = 'disabled'
        patterns = {regex.pattern for regex, _ in self.regex_handlers}
        prefixes = {prefix for prefix, _ in self.prefix_handlers}
        handlers_list = '\n'.join(
            itertools.chain(
                (f'- {path}' for path in self.handlers),
                (f'- REGEX {pattern}' for pattern in patterns),
                (f'- PREFIX {prefix}' for prefix in prefixes),
            ),
        )
        return (
            f'Mockserver handler is not installed for {path!r}.\n'
            'Perhaps you forgot to setup mockserver handler. Run with '
            '--mockserver-nofail flag to suppress these errors.\n'
            f'Tracing: {tracing_state}. Installed handlers:\n'
            f'{handlers_list}'
        )

    async def handle_request(self, request: aiohttp.web.BaseRequest):
        handler, kwargs = self._get_handler_for_request(request)
        try:
            response = await handler(request, **kwargs)
            if isinstance(response, aiohttp.web.Response):
                return response
            raise exceptions.MockServerError(
                'aiohttp.web.Response instance is expected '
                f'{response!r} given',
            )
        except exceptions.HandlerNotFoundError:
            raise
        except http.MockedError as exc:
            return _mocked_error_response(request, exc.error_code)
        except Exception as exc:
            self._report_handler_failure(request.path, exc)
            raise

    def _report_handler_failure(self, path: str, exc: Exception):
        if self.reporter:
            self.reporter.report_error(
                exc, f'Exception in mockserver handler for {path!r}: {exc !r}',
            )

    def register_handler(
            self,
            path: str,
            func,
            *,
            prefix: bool = False,
            regex: bool = False,
    ):
        if regex:
            if prefix:
                raise RuntimeError(
                    'Parameter value prefix=True is not supported if regex '
                    'parameter is also True.',
                )
            pattern = re.compile(path)
            self.regex_handlers.append((pattern, func))
        else:
            if prefix:
                self.prefix_handlers.append((path, func))
            else:
                self.handlers[path] = func
        return func

    def _get_handler_for_request(
            self, request: aiohttp.web.BaseRequest,
    ) -> typing.Tuple[Handler, RouteParams]:
        if self.http_proxy_enabled:
            host = request.headers.get('host')
            if host and host != self.mockserver_host:
                return self.get_handler(f'http://{host}{request.path}')
        return self.get_handler(request.path)


# pylint: disable=too-many-instance-attributes
class Server:
    session = None

    def __init__(
            self,
            mockserver_info: classes.MockserverInfo,
            *,
            nofail=False,
            reporter: typing.Optional[
                reporter_plugin.MockserverReporterPlugin
            ] = None,
            tracing_enabled=True,
            trace_id_header=DEFAULT_TRACE_ID_HEADER,
            span_id_header=DEFAULT_SPAN_ID_HEADER,
            http_proxy_enabled=False,
    ):
        self._info = mockserver_info
        self._nofail = nofail
        self._reporter = reporter
        self._tracing_enabled = tracing_enabled
        self._trace_id_header = trace_id_header
        self._span_id_header = span_id_header
        self._http_proxy_enabled = http_proxy_enabled

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
    def http_proxy_enabled(self):
        return self._http_proxy_enabled

    @property
    def server_info(self) -> classes.MockserverInfo:
        return self._info

    @contextlib.contextmanager
    def new_session(self, trace_id: typing.Optional[str] = None):
        self.session = Session(
            self._reporter,
            tracing_enabled=self._tracing_enabled,
            trace_id=trace_id,
            http_proxy_enabled=self._http_proxy_enabled,
            mockserver_host=self._info.get_host_header(),
        )
        try:
            yield self.session
        finally:
            self.session = None

    async def handle_request(self, request):
        started = time.perf_counter()
        log_level = logging.DEBUG
        fields = {
            '_type': 'mockserver_request',
            'timestamp': datetime.datetime.utcnow(),
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
            log_level = logging.ERROR
            fields['status'] = 'FAIL'
            fields['exc_info'] = str(exc)
            raise
        finally:
            delay_ms = 1000 * (time.perf_counter() - started)
            fields['delay'] = f'{delay_ms:.3f}ms'
            logger.log(log_level, 'Mockserver request', extra={'tskv': fields})

    async def _handle_request(self, request: aiohttp.web.BaseRequest):
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
            raise exceptions.MockServerError(error_message)

        if self.tracing_enabled and _is_other_test(
                trace_id, self.session.trace_id,
        ):
            self._report_other_test_request(request, trace_id)
            return _internal_error(REQUEST_FROM_ANOTHER_TEST_ERROR)
        try:
            return await self.session.handle_request(request)
        except exceptions.HandlerNotFoundError as exc:
            self._report_handler_not_found(exc, nofail=nofail)
            return _internal_error(
                'Internal error: mockserver handler not found',
            )

    def _report_handler_not_found(
            self, exc: exceptions.HandlerNotFoundError, *, nofail: bool,
    ):
        level = logging.WARNING if nofail else logging.ERROR
        logger.log(level, '%s', exc)
        if not nofail and self._reporter is not None:
            self._reporter.report_error(exc)

    def _report_other_test_request(self, request, trace_id):
        logger.warning(
            'Mockserver called path %s with previous test trace_id %s',
            request.path,
            trace_id,
        )


class MockserverFixture:
    """Mockserver handler installer fixture."""

    def __init__(
            self, mockserver: Server, session: Session, base_prefix: str = '',
    ) -> None:
        self._server = mockserver
        self._session = session
        self._base_prefix = base_prefix
        self._base_prefix_re = re.escape(base_prefix)

    def new(self, prefix: str) -> 'MockserverFixture':
        """Create mockserver installer with given base prefix."""
        return MockserverFixture(
            self._server, self._session, self._build_fullpath(prefix),
        )

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
            self,
            path: str,
            *,
            prefix: bool = False,
            raw_request: bool = False,
            json_response: bool = False,
            regex: bool = False,
    ) -> classes.GenericRequestDecorator:
        """Register basic http handler for ``path``.

        Returns decorator that registers handler ``path``. Original function is
        wrapped with :ref:`AsyncCallQueue`.

        :param path: match url by prefix if ``True`` exact match otherwise
        :param raw_request: pass ``aiohttp.web.Response`` to handler instead of
            ``testsuite.utils.http.Request``
        :param regex: set True to match path as regex pattern
        :param prefix: set True to match path prefix instead of whole path
        :param json_response: set True to let handler return json object
               instead of full response object

        .. code-block:: python

           @mockserver.handler('/service/path')
           def handler(request: testsuite.utils.http.Request):
               return mockserver.make_response('Hello, world!')
        """

        if raw_request:
            warnings.warn(
                'raw_request=True is deprecated, '
                'use aiohttp_handler() instead',
                DeprecationWarning,
            )
        if json_response:
            warnings.warn(
                'json_response=True is deprecated, '
                'use json_handler() instead',
                DeprecationWarning,
            )

        return self._handler_installer(
            path,
            prefix=prefix,
            raw_request=raw_request,
            json_response=json_response,
            regex=regex,
        )

    def json_handler(
            self,
            path: str,
            *,
            prefix: bool = False,
            raw_request: bool = False,
            regex: bool = False,
    ) -> classes.JsonRequestDecorator:
        """Register json http handler for ``path``.

        Returns decorator that registers handler ``path``. Original function is
        wrapped with :ref:`AsyncCallQueue`.

        :param path: match url by prefix if ``True`` exact match otherwise
        :param raw_request: pass ``aiohttp.web.Response`` to handler instead of
            ``testsuite.utils.http.Request``
        :param prefix: set True to match path prefix instead of whole path
        :param regex: set True to match path as regex pattern

        .. code-block:: python

           @mockserver.json_handler('/service/path')
           def handler(request: testsuite.utils.http.Request):
               # Return JSON document
               return {...}
               # or call to mockserver.make_response()
               return mockserver.make_response(...)
        """
        if raw_request:
            warnings.warn(
                'raw_request=True is deprecated, '
                'use aiohttp_json_handler() instead',
                DeprecationWarning,
            )
        return self._handler_installer(
            path,
            prefix=prefix,
            raw_request=raw_request,
            json_response=True,
            regex=regex,
        )

    def aiohttp_handler(
            self, path: str, *, prefix: bool = False, regex: bool = False,
    ) -> classes.GenericRequestDecorator:
        return self._handler_installer(
            path,
            prefix=prefix,
            raw_request=True,
            json_response=False,
            regex=regex,
        )

    def aiohttp_json_handler(
            self, path: str, *, prefix: bool = False, regex: bool = False,
    ) -> classes.JsonRequestDecorator:
        return self._handler_installer(
            path,
            prefix=prefix,
            raw_request=True,
            json_response=True,
            regex=regex,
        )

    def url(self, path: str) -> str:
        """Builds mockserver url for ``path``"""
        return url_util.join(self.base_url, path)

    def ignore_trace_id(self) -> typing.ContextManager[None]:
        return self.tracing(False)

    @contextlib.contextmanager
    def tracing(self, value: bool = True):
        original_value = self._session.tracing_enabled
        try:
            self._session.tracing_enabled = value
            yield
        finally:
            self._session.tracing_enabled = original_value

    def get_callqueue_for(self, path) -> callinfo.AsyncCallQueue:
        handler, _ = self._session.get_handler(path)
        return handler.callqueue

    make_response = staticmethod(http.make_response)

    TimeoutError = http.TimeoutError
    NetworkError = http.NetworkError

    def _handler_installer(
            self,
            path: str,
            *,
            prefix: bool = False,
            raw_request: bool = False,
            json_response: bool = False,
            regex: bool = False,
    ) -> typing.Callable:
        path = self._build_fullpath(path, regex)

        def decorator(func):
            handler = Handler(
                func, raw_request=raw_request, json_response=json_response,
            )
            self._session.register_handler(
                path, handler, prefix=prefix, regex=regex,
            )
            return handler.callqueue

        return decorator

    def _build_fullpath(self, path, regex: bool = False) -> str:
        if regex:
            return self._base_prefix_re + path
        if not self._base_prefix or self._base_prefix.endswith('/'):
            if self._server.http_proxy_enabled and path.startswith('http://'):
                return path
            return url_util.join(self._base_prefix, path)
        return self._base_prefix + path


MockserverSslFixture = MockserverFixture


def _create_ssl_context(ssl_info: classes.SslCertInfo) -> ssl.SSLContext:
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(ssl_info.cert_path, ssl_info.private_key_path)
    return ssl_context


def _internal_error(message: str = 'Internal error') -> aiohttp.web.Response:
    return http.make_response(message, status=500)


def _mocked_error_response(request, error_code) -> aiohttp.web.Response:
    if _SUPPORTED_ERRORS_HEADER not in request.headers:
        raise exceptions.MockServerError(
            'Service does not support mockserver errors protocol',
        )
    supported_errors = request.headers[_SUPPORTED_ERRORS_HEADER].split(',')
    if error_code not in supported_errors:
        raise exceptions.MockServerError(
            f'Service does not support mockserver error of type {error_code}',
        )
    return http.make_response(
        response='', status=599, headers={_ERROR_HEADER: error_code},
    )


@compat.asynccontextmanager
async def create_server(
        host: str,
        port: int,
        loop,
        testsuite_logger,
        mockserver_reporter: reporter_plugin.MockserverReporterPlugin,
        pytestconfig,
        ssl_info: typing.Optional[classes.SslCertInfo],
) -> typing.AsyncGenerator[Server, None]:
    ssl_context: typing.Optional[ssl.SSLContext]
    if ssl_info:
        ssl_context = _create_ssl_context(ssl_info)
    else:
        ssl_context = None

    async with net_utils.create_tcp_server(
            lambda: web_server(), host=host, port=port, ssl=ssl_context,
    ) as aio_server:
        mockserver_info = _create_mockserver_info(
            aio_server.sockets[0], host, ssl_info,
        )
        server = Server(
            mockserver_info,
            nofail=pytestconfig.option.mockserver_nofail,
            reporter=mockserver_reporter,
            tracing_enabled=pytestconfig.getini('mockserver-tracing-enabled'),
            trace_id_header=pytestconfig.getini('mockserver-trace-id-header'),
            span_id_header=pytestconfig.getini('mockserver-span-id-header'),
            http_proxy_enabled=pytestconfig.getini(
                'mockserver-http-proxy-enabled',
            ),
        )
        web_server = aiohttp.web.Server(
            server.handle_request, loop=loop, access_log=None,
        )
        yield server


def _create_mockserver_info(
        sock, host: str, ssl_info: typing.Optional[classes.SslCertInfo],
) -> classes.MockserverInfo:
    sock_address = sock.getsockname()
    schema = 'https' if ssl_info else 'http'
    port = sock_address[1]
    base_url = '%s://%s:%d/' % (schema, host, port)
    return classes.MockserverInfo(
        host=host, port=port, base_url=base_url, ssl=ssl_info,
    )


def generate_trace_id() -> str:
    return _TRACE_ID_PREFIX + uuid.uuid4().hex


def _is_from_client_fixture(trace_id: str) -> bool:
    return trace_id is not None and trace_id.startswith(_TRACE_ID_PREFIX)


def _is_other_test(trace_id: str, current_trace_id: str) -> bool:
    return trace_id != current_trace_id and _is_from_client_fixture(trace_id)
