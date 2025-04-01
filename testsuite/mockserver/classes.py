from __future__ import annotations

import dataclasses
import pathlib
import typing

import aiohttp.web

from testsuite import type_annotations
from testsuite.utils import callinfo, http, url_util

GenericRequestHandler = typing.Callable[
    ...,
    type_annotations.MaybeAsyncResult[aiohttp.web.Response],
]
GenericRequestDecorator = typing.Callable[
    [GenericRequestHandler],
    callinfo.AsyncCallQueue,
]
JsonRequestHandler = typing.Callable[
    ...,
    type_annotations.MaybeAsyncResult[
        typing.Union[aiohttp.web.Response, type_annotations.JsonAnyOptional]
    ],
]
JsonRequestDecorator = typing.Callable[
    [JsonRequestHandler],
    callinfo.AsyncCallQueue,
]
MockserverRequest = http.Request


@dataclasses.dataclass(frozen=True)
class SslCertInfo:
    cert_path: str
    private_key_path: str


@dataclasses.dataclass(frozen=True)
class MockserverInfo:
    host: str | None
    port: int | None
    base_url: str
    ssl: SslCertInfo | None
    socket_path: pathlib.Path | None = None

    def url(self, path: str) -> str:
        """Concats ``base_url`` and provided ``path``."""
        return url_util.join(self.base_url, path)

    def get_host_header(self) -> str:
        if self.socket_path:
            return str(self.socket_path)

        if not self.host and not self.port:
            raise RuntimeError(
                'either host and port or socket_path must be set in mockserver info'
            )

        if self.port == 80:
            return str(self.host)
        return f'{self.host}:{self.port}'


class MockserverSslInfo(MockserverInfo):
    ssl: SslCertInfo


MockserverInfoFixture = MockserverInfo
MockserverSslInfoFixture = typing.Optional[MockserverInfo]
