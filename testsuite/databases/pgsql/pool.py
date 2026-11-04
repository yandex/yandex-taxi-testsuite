import contextlib
import typing

import psycopg
import psycopg_pool


class AutocommitConnectionPool:
    def __init__(self, minconn: int, maxconn: int, uri: str) -> None:
        self._pool = psycopg_pool.ConnectionPool(
            uri,
            min_size=minconn,
            max_size=maxconn,
            kwargs={'autocommit': True},
            open=True,
        )

    @contextlib.contextmanager
    def get_connection(
        self,
    ) -> typing.Generator[psycopg.Connection, None, None]:
        with self._pool.connection() as conn:
            yield conn

    def close(self) -> None:
        self._pool.close()
