import typing

import pytest

from testsuite.utils import callinfo


class TestpointSession:
    """Testpoint control object."""

    def __init__(self):
        self._handlers = {}

    def get_handler(
            self, name: str,
    ) -> typing.Optional[callinfo.AsyncCallQueue]:
        return self._handlers.get(name)

    def __getitem__(self, name: str) -> callinfo.AsyncCallQueue:
        return self._handlers[name]

    def __call__(
            self, name: str,
    ) -> typing.Callable[[typing.Callable], callinfo.AsyncCallQueue]:
        """Returns decorator for registering testpoint called ``name``.

        After decoration function is wrapped with `AsyncCallQueue`_.

        """

        def decorator(func) -> callinfo.AsyncCallQueue:
            wrapped = callinfo.acallqueue(func)
            self._handlers[name] = wrapped
            return wrapped

        return decorator


@pytest.fixture
def testpoint(mockserver) -> TestpointSession:
    """Testpoint fixture returns testpoint session instance that works
    as decorator that registers testpoint handler. Original function is
    wrapped with :ref:`AsyncCallQueue`

    :param name: testpoint name
    :returns: decorator

    .. code-block::

       def test_foo(testpoint):
           @testpoint('foo'):
           def testpoint_handler(data):
               pass

           ...
           # testpoint_handler is AsyncCallQueue instance, e.g.:
           assert testpoint_handler.has_calls
           assert testpoint_handler.next_call == {...}
           aseert testpoint_handler.wait_call() == {...}
    """

    session = TestpointSession()

    @mockserver.json_handler('/testpoint')
    async def _handler(request):
        body = request.json
        handler = session.get_handler(body['name'])
        if handler is not None:
            data = await handler(body['data'])
        else:
            data = None
        return {'data': data}

    return session
