"""
Utilities for attaching typed marks to pytest fixture functions
and querying those marks during a test session.

Use :func:`mark` to store an info object on the original function.
Use :func:`get_infos` to retrieve fixtures tagged with a particular
info type among those visible to a request.

Marks are independent of ``@pytest.fixture``: apply the mark to the
original function, then wrap with ``@pytest.fixture``.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator, Sequence
from typing import Any, TypeVar, cast

import pytest

__all__ = [
    'get_infos',
    'mark',
]

I = TypeVar('I')  # noqa: E741

_MARKS_ATTR = '_testsuite_fixture_marks'
_SCOPE_RANK = {
    'function': 0,
    'class': 1,
    'module': 2,
    'package': 3,
    'session': 4,
}


def mark(
    func: Callable[..., object],
    info: object,
    /,
) -> Callable[..., object]:
    """
    Attach *info* to the original function *func*.

    Creates the marks dict if it is missing, otherwise updates it.
    The *info* type is the lookup key for :func:`get_infos`. Each type
    may be attached at most once.

    *func* must be the original function, not a ``@pytest.fixture``
    wrapper. Typical use is a thin decorator that calls :func:`mark`
    and is stacked under ``@pytest.fixture``::

        @dataclass
        class SqlSeed:
            order: int

        def sql_seed(*, order: int = 0):
            def decorator(function):
                return mark(function, SqlSeed(order=order))
            return decorator

        @pytest.fixture
        @sql_seed()
        def seed_users(pgsql):
            pgsql['mydb'].execute('INSERT INTO users ...')

        @pytest.fixture(name='seed_orders')
        @sql_seed(order=1)
        def _seed_orders(pgsql):
            pgsql['mydb'].execute('INSERT INTO orders ...')

    :param func: The original fixture function.
    :param info: Metadata instance to store.
    :returns: *func*, unchanged.
    """
    if _is_pytest_fixture_wrapper(func):
        name = getattr(func, '__qualname__', func.__name__)
        raise ValueError(
            f'{name!r} is already wrapped by @pytest.fixture; '
            'apply the mark under @pytest.fixture, not above it',
        )

    marks = getattr(func, _MARKS_ATTR, None)
    if marks is None:
        marks = {}
        setattr(func, _MARKS_ATTR, marks)
    info_type = type(info)
    if (existing := marks.get(info_type)) is not None:
        name = getattr(func, '__qualname__', func.__name__)
        raise ValueError(
            f'{name!r} already has a {info_type.__name__} mark '
            f'({existing!r}); cannot attach another ({info!r})',
        )
    marks[info_type] = info
    return func


def get_infos(
    request: pytest.FixtureRequest,
    info_type: type[I],
    /,
) -> dict[str, I]:
    """
    Return marked fixtures of *info_type* that are visible to a request.

    Walks fixture definitions known to pytest, keeps those applicable to
    the requesting test, and skips fixtures whose scope is narrower than
    ``request.scope``.

    Only the winning fixture definition is inspected. An override must
    carry its own mark; a parent mark is not inherited.

    Continuing the ``SqlSeed`` example::

        seeds = get_infos(request, SqlSeed)
        ordered = sorted(seeds.items(), key=lambda kv: kv[1].order)
        for name, _info in ordered:
            # Pulls ``pgsql`` through the seed fixture's own
            # dependencies.
            request.getfixturevalue(name)

    :param request: The pytest fixture request object.
    :param info_type: The info class whose tagged fixtures you want
        to look up.
    :returns: ``dict[str, I]`` mapping each tagged fixture's name to the
        *info* object that was passed to :func:`mark`.
        The dict is a fresh copy; mutating it has no effect on stored
        data.
    """
    collected: dict[str, I] = {}
    for fixturedef in _iter_visible_fixtures(request):
        marks = getattr(fixturedef.func, _MARKS_ATTR, None)
        if not marks:
            continue
        info = marks.get(info_type)
        if type(info) is info_type:
            collected[fixturedef.argname] = cast(I, info)
    return collected


def _is_pytest_fixture_wrapper(func: object) -> bool:
    if getattr(func, '_pytestfixturefunction', None):
        return True
    return type(func).__name__ == 'FixtureFunctionDefinition'


def _get_fixturedefs(
    fixture_manager: Any,
    name: str,
    request: pytest.FixtureRequest,
) -> Sequence[Any] | None:
    item = request._pyfuncitem
    params = inspect.signature(fixture_manager.getfixturedefs).parameters
    key = item if list(params)[1] == 'node' else item.nodeid
    return fixture_manager.getfixturedefs(name, key)


def _iter_visible_fixtures(
    request: pytest.FixtureRequest,
) -> Iterator[pytest.FixtureDef[Any]]:
    fixture_manager = request.session._fixturemanager
    invoking_rank = _SCOPE_RANK[request.scope]

    for name in fixture_manager._arg2fixturedefs:
        matched = _get_fixturedefs(fixture_manager, name, request)
        if not matched:
            continue
        winning = matched[-1]
        if _SCOPE_RANK[winning.scope] < invoking_rank:
            continue
        yield winning
