import contextlib
import typing
import uuid

import aiohttp

from testsuite import utils
from testsuite.utils import http
from testsuite.utils import url_util

DEFAULT_HOST = 'localhost'
DEFAULT_TIMEOUT = 120.0


class Descriptor(typing.NamedTuple):
    service_name: str
    run_module_path: str
    host: str
    port: int

    @property
    def base_url(self):
        return 'http://%s:%d' % (self.host, self.port)


class Client:
    """Basic asyncio HTTP service client."""

    session: aiohttp.ClientSession

    def __init__(
            self,
            base_url: str,
            *,
            session: aiohttp.ClientSession,
            ssl_context=None,
            span_id_header=None,
            default_headers: typing.Optional[typing.Dict[str, str]] = None,
            service_headers=None,
            timeout: float = DEFAULT_TIMEOUT,
            raw_response=False,
    ):
        """
        :param base_url: Base client url
        :param session: ``aiohttp.ClientSession`` instance
        :param default_headers: default request headers dictionary
        :param timeout: http client default timeout
        """
        self.base_url = url_util.ensure_trailing_separator(base_url)
        self.default_headers = default_headers or {}
        self.service_headers = service_headers or {}
        self.timeout = timeout
        self.session = session
        self._ssl_context = ssl_context
        self._span_id_header = span_id_header
        self._raw_response = raw_response

    async def _request(
            self,
            http_method,
            path,
            headers=None,
            bearer=None,
            x_real_ip=None,
            **kwargs,
    ):
        url = url_util.join(self.base_url, path)
        headers = self._build_headers(
            headers,
            service_headers=self.service_headers,
            bearer=bearer,
            x_real_ip=x_real_ip,
        )
        kwargs['timeout'] = kwargs.get('timeout', self.timeout)

        params = kwargs.get('params', None)
        if params is not None:
            kwargs['params'] = _flatten(params)
        response = await self.session.request(
            http_method,
            url,
            headers=headers,
            ssl_context=self._ssl_context,
            **kwargs,
        )
        if self._raw_response:
            return response
        wrapped = await http.wrap_client_response(response)
        return wrapped

    async def post(
            self,
            path,
            json=None,
            data=None,
            params=None,
            bearer=None,
            x_real_ip=None,
            headers=None,
            **kwargs,
    ):
        """Perform HTTP POST request."""
        return await self._request(
            'POST',
            path,
            json=json,
            data=data,
            params=params,
            headers=headers,
            bearer=bearer,
            x_real_ip=x_real_ip,
            **kwargs,
        )

    async def put(
            self,
            path,
            json=None,
            data=None,
            params=None,
            bearer=None,
            x_real_ip=None,
            headers=None,
            **kwargs,
    ):
        """Perform HTTP PUT request."""
        return await self._request(
            'PUT',
            path,
            json=json,
            data=data,
            params=params,
            headers=headers,
            bearer=bearer,
            x_real_ip=x_real_ip,
            **kwargs,
        )

    async def patch(
            self,
            path,
            json=None,
            data=None,
            params=None,
            bearer=None,
            x_real_ip=None,
            headers=None,
            **kwargs,
    ):
        """Perform HTTP PATCH request."""
        return await self._request(
            'PATCH',
            path,
            json=json,
            data=data,
            params=params,
            headers=headers,
            bearer=bearer,
            x_real_ip=x_real_ip,
            **kwargs,
        )

    async def get(
            self, path, headers=None, bearer=None, x_real_ip=None, **kwargs,
    ):
        """Perform HTTP GET request."""
        return await self._request(
            'GET',
            path,
            headers=headers,
            bearer=bearer,
            x_real_ip=x_real_ip,
            **kwargs,
        )

    async def delete(
            self, path, headers=None, bearer=None, x_real_ip=None, **kwargs,
    ):
        """Perform HTTP DELETE request."""
        return await self._request(
            'DELETE',
            path,
            headers=headers,
            bearer=bearer,
            x_real_ip=x_real_ip,
            **kwargs,
        )

    async def options(
            self, path, headers=None, bearer=None, x_real_ip=None, **kwargs,
    ):
        """Perform HTTP OPTIONS request."""
        return await self._request(
            'OPTIONS',
            path,
            headers=headers,
            bearer=bearer,
            x_real_ip=x_real_ip,
            **kwargs,
        )

    async def request(self, http_method: str, path: str, **kwargs):
        """Perform HTTP ``http_method`` request."""
        return await self._request(http_method, path, **kwargs)

    def _build_headers(
            self,
            user_headers=None,
            service_headers=None,
            bearer=None,
            x_real_ip=None,
    ):
        headers = self.default_headers.copy()
        if service_headers is not None:
            headers.update(service_headers)
        if user_headers:
            headers.update(user_headers)
        if bearer:
            headers['Authorization'] = 'Bearer %s' % bearer
        if x_real_ip:
            headers['X-Real-IP'] = x_real_ip
        if self._span_id_header and self._span_id_header not in headers:
            headers[self._span_id_header] = uuid.uuid4().hex

        headers = {
            key: '' if value is None else value
            for key, value in headers.items()
        }
        return headers


class ClientTestsControl(Client):
    """Asyncio client for services with tests/control method support.

    Performs lazy call to tests/control on first service call.
    """

    def __init__(
            self,
            base_url,
            *,
            mocked_time,
            span_id_header=None,
            raw_response=False,
            **kwargs,
    ):
        super(ClientTestsControl, self).__init__(
            base_url,
            span_id_header=span_id_header,
            raw_response=raw_response,
            **kwargs,
        )
        self._caches_dirty = True
        self._mocked_time = mocked_time

    async def _prepare(self):
        if self._caches_dirty:
            await self.invalidate_caches()

    async def _request(
            self,
            http_method,
            path,
            headers=None,
            bearer=None,
            x_real_ip=None,
            **kwargs,
    ):
        await self._prepare()
        return await super(ClientTestsControl, self)._request(
            http_method, path, headers, bearer, x_real_ip, **kwargs,
        )

    async def tests_control(
            self,
            invalidate_caches: bool = True,
            clean_update: bool = True,
            cache_names: typing.Optional[typing.List[str]] = None,
    ):
        now = self._mocked_time.now()

        response = await self.post(
            '/tests/control',
            {
                'now': utils.timestring(now),
                'invalidate_caches': invalidate_caches,
                'cache_clean_update': clean_update,
                **({'names': cache_names} if cache_names else {}),
            },
        )
        response.raise_for_status()
        return response

    async def invalidate_caches(
            self,
            clean_update: bool = True,
            cache_names: typing.Optional[typing.List[str]] = None,
    ):
        if clean_update and not cache_names:
            with self._safe_clear_caches_dirty():
                await self.tests_control(
                    invalidate_caches=True, clean_update=True,
                )
        else:
            await self.tests_control(
                invalidate_caches=True,
                clean_update=clean_update,
                cache_names=cache_names,
            )

    @contextlib.contextmanager
    def _safe_clear_caches_dirty(self):
        original, self._caches_dirty = self._caches_dirty, False
        try:
            yield
        except Exception:
            self._caches_dirty = original
            raise


def _flatten(query_params):
    result = []
    iterable = (
        query_params.items()
        if isinstance(query_params, dict)
        else query_params
    )
    for key, value in iterable:
        if isinstance(value, (tuple, list)):
            for element in value:
                result.append((key, str(element)))
        else:
            result.append((key, str(value)))
    return result
