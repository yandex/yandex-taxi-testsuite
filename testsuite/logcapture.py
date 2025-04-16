from __future__ import annotations

import asyncio
import contextlib
import enum
import logging
import typing

from testsuite.utils import callinfo, traceback

logger = logging.getLogger(__name__)


class BaseError(Exception):
    pass


class IncorrectUsageError(BaseError):
    pass


class ClientConnectTimeoutError(BaseError):
    pass


class TimeoutError(BaseError):
    pass


class LogLevel(enum.Enum):
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5
    NONE = 6

    @classmethod
    def from_string(cls, level: str) -> 'LogLevel':
        return cls[level.upper()]


class CapturedLogs:
    def __init__(self, *, log_level: LogLevel) -> None:
        self._log_level = log_level
        self._logs: list[dict] = []
        self._subscribers = []
        self._closed = False

    @property
    def log_level(self):
        return self._log_level

    def is_closed(self):
        return self._closed

    def close(self):
        self._closed = True

    async def publish(self, row: dict) -> None:
        self._logs.append(row)
        for query, callback in self._subscribers:
            if _match_entry(row, query):
                await callback(**row)

    def subscribe(self, query: dict, decorated):
        self._subscribers.append((query, decorated))

    def __iter__(self) -> typing.Iterator[dict]:
        return iter(self._logs)


class Capture:
    def __init__(self, logs: CapturedLogs):
        self._logs = logs

    def select(self, **query) -> list[dict]:
        if not self._logs.is_closed():
            raise IncorrectUsageError(
                'select() is only supported for closed captures\n'
                'Please move select() after context manager body',
            )
        level = query.get('level')
        if level:
            log_level = LogLevel[level]
            if log_level.value < self._logs.log_level.value:
                raise IncorrectUsageError(
                    f'Requested log level={log_level.name} is lower than service log level {self._logs.log_level.name}',
                )
        result = []
        for row in self._logs:
            if _match_entry(row, query):
                result.append(row)
        return result

    def subscribe(self, **query):
        if self._logs.is_closed():
            raise IncorrectUsageError(
                'subscribe() is not supported for closed captures\nPlease move subscribe() into context manager body',
            )

        def decorator(func):
            decorated = callinfo.acallqueue(func)
            self._logs.subscribe(query, decorated)
            return decorated

        return decorator


class CaptureServer:
    _capture: CapturedLogs | None

    def __init__(self, *, log_level: str, parse_line):
        self._log_level = LogLevel.from_string(log_level)
        self._client_cond = asyncio.Condition()
        self._capture = None
        self._tasks = []
        self._parse_line = parse_line
        self._started = False
        self._socknames = []

    def getsocknames(self):
        return self._socknames

    @contextlib.asynccontextmanager
    async def start(self, *args, **kwargs):
        if self._started:
            raise IncorrectUsageError('Service was already started')
        server = await asyncio.start_server(
            self._handle_client, *args, **kwargs
        )
        self._started = True
        self._socknames = [sock.getsockname() for sock in server.sockets]
        try:
            yield self
        finally:
            server.close()
            await server.wait_closed()

    async def wait_for_client(self, timeout: float = 10.0):
        async def waiter():
            async with self._client_cond:
                await self._client_cond.wait_for(lambda: self._tasks)

        logger.debug('Waiting for logcapture client to connect...')
        try:
            await asyncio.wait_for(waiter(), timeout=timeout)
        except TimeoutError:
            raise ClientConnectTimeoutError(
                'Timedout while waiting for logcapture client to connect',
            )

    async def _handle_client(self, reader, writer):
        logger.debug('logcapture client connected')

        async def log_reader(capture: CapturedLogs):
            with contextlib.closing(writer):
                async for line in reader:
                    row = self._parse_line(line)
                    await capture.publish(row)
            await writer.wait_closed()

        if not self._capture:
            writer.close()
            await writer.wait_closed()
        else:
            self._tasks.append(asyncio.create_task(log_reader(self._capture)))
            async with self._client_cond:
                self._client_cond.notify_all()

    @contextlib.asynccontextmanager
    async def capture(
        self,
        *,
        log_level: str | None = None,
        timeout: float = 10.0,
    ) -> typing.AsyncIterator[CapturedLogs]:
        if self._capture:
            yield self._capture
            return

        if not log_level:
            actual_log_level = self._log_level
        else:
            actual_log_level = LogLevel.from_string(log_level)

        self._capture = CapturedLogs(log_level=actual_log_level)
        try:
            yield Capture(self._capture)
        finally:
            self._capture.close()
            self._capture = None
            if self._tasks:
                _, pending = await asyncio.wait(self._tasks, timeout=timeout)
                self._tasks = []
                if pending:
                    raise TimeoutError(
                        'Timeout while waiting for capture task to finish',
                    )


def _match_entry(row: dict, query: dict) -> bool:
    for key, value in query.items():
        if row.get(key) != value:
            return False
    return True


__tracebackhide__ = traceback.hide(BaseError, FileNotFoundError)
