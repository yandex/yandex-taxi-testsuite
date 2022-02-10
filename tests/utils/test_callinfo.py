# pylint: disable=blacklisted-name,eval-used
import asyncio
import functools

import pytest

from testsuite.utils import callinfo


def test_callinfo():
    def noargs():
        pass

    getter = callinfo.callinfo(noargs)
    assert getter((), {}) == {}

    def positional(arg_a, arg_b):
        pass

    getter = callinfo.callinfo(positional)
    assert getter((1, 2), {}) == {'arg_a': 1, 'arg_b': 2}
    assert getter((1,), {'arg_b': 2}) == {'arg_a': 1, 'arg_b': 2}
    assert getter((), {'arg_a': 1, 'arg_b': 2}) == {'arg_a': 1, 'arg_b': 2}

    def positional_keyword(arg_a, arg_b, arg_c=3):
        pass

    getter = callinfo.callinfo(positional_keyword)
    assert getter((1, 2), {}) == {'arg_a': 1, 'arg_b': 2, 'arg_c': 3}
    assert getter((1, 2, 4), {}) == {'arg_a': 1, 'arg_b': 2, 'arg_c': 4}
    assert getter((1,), {'arg_b': 2, 'arg_c': 4}) == {
        'arg_a': 1,
        'arg_b': 2,
        'arg_c': 4,
    }

    def starargs(*args, **kwargs):
        pass

    getter = callinfo.callinfo(starargs)
    assert getter((1, 2), {}) == {'args': (1, 2), 'kwargs': {}}
    assert getter((1, 2), {'k': 'v'}) == {'args': (1, 2), 'kwargs': {'k': 'v'}}

    def mixed(arg_a, arg_b, arg_c=3, **kwargs):
        pass

    getter = callinfo.callinfo(mixed)
    assert getter((1, 2), {}) == {
        'arg_a': 1,
        'arg_b': 2,
        'arg_c': 3,
        'kwargs': {},
    }
    assert getter((1,), {'arg_z': 3, 'arg_b': 2, 'arg_c': 4}) == {
        'arg_a': 1,
        'arg_b': 2,
        'arg_c': 4,
        'kwargs': {'arg_z': 3},
    }

    kwonlyargs = eval('lambda a, *args, b, c=3, **kwargs: None')
    getter = callinfo.callinfo(kwonlyargs)
    assert getter((4,), {'b': 5}) == {
        'a': 4,
        'args': (),
        'b': 5,
        'c': 3,
        'kwargs': {},
    }
    assert getter((4,), {'b': 5, 'c': 2}) == {
        'a': 4,
        'args': (),
        'b': 5,
        'c': 2,
        'kwargs': {},
    }
    assert getter((4, 5, 6), {'b': 5}) == {
        'a': 4,
        'args': (5, 6),
        'b': 5,
        'c': 3,
        'kwargs': {},
    }
    assert getter((4, 5, 6), {'b': 5, 'c': 6}) == {
        'a': 4,
        'args': (5, 6),
        'b': 5,
        'c': 6,
        'kwargs': {},
    }
    assert getter((4, 5, 6), {'b': 5, 'c': 6, 'd': 7}) == {
        'a': 4,
        'args': (5, 6),
        'b': 5,
        'c': 6,
        'kwargs': {'d': 7},
    }


def test_callinfo_wrapped():
    def foo(a, b, c):
        pass

    getter = callinfo.callinfo(foo)
    assert getter((1, 2, 3), {}) == {'a': 1, 'b': 2, 'c': 3}

    @functools.wraps(foo)
    def bar(*args, **kwargs):
        pass

    getter = callinfo.callinfo(bar)
    assert getter((1, 2, 3), {}) == {'a': 1, 'b': 2, 'c': 3}


async def test_callqueue_wait():
    @callinfo.acallqueue
    def method(arg):
        pass

    async def async_task():
        await method(1)
        await asyncio.sleep(0.1)
        await method(2)

    asyncio.create_task(async_task())

    assert await method.wait_call() == {'arg': 1}
    assert await method.wait_call() == {'arg': 2}


async def test_callqueue_wait_timeout():
    @callinfo.acallqueue
    def method(arg):
        pass

    with pytest.raises(callinfo.CallQueueTimeoutError):
        assert await method.wait_call(timeout=0.1)


async def test_callqueue_next_call():
    @callinfo.acallqueue
    def method(arg):
        pass

    assert not method.has_calls
    with pytest.raises(callinfo.CallQueueEmptyError):
        assert await method.next_call()

    await method(1)
    await method(2)

    assert method.has_calls
    assert method.times_called == 2

    assert method.next_call() == {'arg': 1}
    assert method.next_call() == {'arg': 2}

    assert not method.has_calls
    with pytest.raises(callinfo.CallQueueEmptyError):
        assert method.next_call()


async def test_acallqueue_next_call():
    @callinfo.acallqueue
    async def method(arg):
        pass

    assert not method.has_calls
    with pytest.raises(callinfo.CallQueueEmptyError):
        assert method.next_call()

    await method(1)
    await method(2)

    assert method.has_calls
    assert method.times_called == 2

    assert method.next_call() == {'arg': 1}
    assert method.next_call() == {'arg': 2}

    assert not method.has_calls
    with pytest.raises(callinfo.CallQueueEmptyError):
        assert method.next_call()


async def test_acallqueue_with_static_method():
    class SomeClass:
        @callinfo.acallqueue
        @staticmethod
        def method(arg):
            pass

    async def async_task():
        await SomeClass.method(1)
        await SomeClass.method(2)

    asyncio.create_task(async_task())

    assert await SomeClass.method.wait_call() == {'arg': 1}
    assert await SomeClass.method.wait_call() == {'arg': 2}


def test_getfullargspec():
    def foo(a, b, c):
        pass

    @functools.wraps(foo)
    def bar(a, b, c):
        pass

    @functools.wraps(bar)
    def maurice(a, b, c):
        pass

    assert callinfo.getfullargspec(foo).args == ['a', 'b', 'c']
    assert callinfo.getfullargspec(bar).args == ['a', 'b', 'c']
    assert callinfo.getfullargspec(maurice).args == ['a', 'b', 'c']
