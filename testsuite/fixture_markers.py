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

import itertools
import inspect
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, cast

import pytest

__all__ = [
    'get_infos',
    'mark',
]

I = TypeVar('I')  # noqa: E741

_MARKS_ATTR = '_testsuite_fixture_marks'
_MARKS_ORDER_ATTR = '_testsuite_fixture_marks_order'
_mark_order_counter = itertools.count()
_SCOPE_RANK = {
    'function': 0,
    'class': 1,
    'module': 2,
    'package': 3,
    'session': 4,
}


@dataclass(frozen=True, order=True)
class _SortKey:
    has_location: bool
    site_rank: int
    stamp: int


@dataclass(frozen=True)
class _MarkedFixture(Generic[I]):
    sort_key: _SortKey
    name: str
    info: I


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
    wrapper. Apply the mark under ``@pytest.fixture``.

    See :doc:`fixture_markers` for usage examples.

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
    # Decorations run in definition order within a module; pytest later
    # registers fixtures via dir(), which is alphabetical — stamp order here.
    if getattr(func, _MARKS_ORDER_ATTR, None) is None:
        setattr(func, _MARKS_ORDER_ATTR, next(_mark_order_counter))
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

    The winning fixture definition is the one pytest would call. If it
    has no mark of *info_type*, the mark is inherited from the nearest
    overridden definition that has one. A mark on the winner replaces
    the inherited mark. There is no way to drop an inherited mark.

    Fixtures within a single module are ordered by definition order. An
    override takes the position of the original fixture in that order — it
    is inserted in place of the fixture it overrides.

    Fixtures from different modules follow the usual pytest definition-site
    priorities: non-conftest plugins (registration order), then conftest
    modules from outer to inner (less specific first, same as pytest
    override chains), then test modules, then test classes.

    See :doc:`fixture_markers` for usage examples.

    :param request: The pytest fixture request object.
    :param info_type: The info class whose tagged fixtures you want
        to look up.
    :returns: ``dict[str, I]`` mapping each tagged fixture's name to the
        *info* object that was passed to :func:`mark`.
        The dict is a fresh copy; mutating it has no effect on stored
        data.
    """
    site_ranks = _definition_site_ranks(request._pyfuncitem)
    collected: list[_MarkedFixture[I]] = []
    for fixturedef in _iter_visible_fixtures(request):
        marked = _marked_fixture_for_name(
            request,
            fixturedef.argname,
            info_type,
            site_ranks,
        )
        if marked is not None:
            collected.append(marked)
    collected.sort(key=lambda item: item.sort_key)
    return {item.name: item.info for item in collected}


def _is_pytest_fixture_wrapper(func: object) -> bool:
    if getattr(func, '_pytestfixturefunction', None):
        return True
    return type(func).__name__ == 'FixtureFunctionDefinition'


def _get_fixturedefs(
    fixture_manager: Any,
    name: str,
    request: pytest.FixtureRequest,
) -> Sequence[pytest.FixtureDef[object]] | None:
    item = request._pyfuncitem
    params = inspect.signature(fixture_manager.getfixturedefs).parameters
    key = item if list(params)[1] == 'node' else item.nodeid
    return fixture_manager.getfixturedefs(name, key)


def _iter_visible_fixtures(
    request: pytest.FixtureRequest,
) -> Iterator[pytest.FixtureDef[object]]:
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


def _marked_fixture_for_name(
    request: pytest.FixtureRequest,
    name: str,
    info_type: type[I],
    site_ranks: Mapping[str, int],
) -> _MarkedFixture[I] | None:
    fixture_manager = request.session._fixturemanager
    matched = _get_fixturedefs(fixture_manager, name, request)
    if not matched:
        return None
    info = _inherited_info(matched, info_type)
    if info is None:
        return None
    return _MarkedFixture(
        sort_key=_sort_key(matched, info_type, site_ranks),
        name=name,
        info=info,
    )


def _inherited_info(
    matched: Sequence[pytest.FixtureDef[object]],
    info_type: type[I],
) -> I | None:
    # matched is ordered from the least specific definition to the winner.
    for fixturedef in reversed(matched):
        info = _mark_info(fixturedef, info_type)
        if info is not None:
            return info
    return None


def _sort_key(
    matched: Sequence[pytest.FixtureDef[object]],
    info_type: type[I],
    site_ranks: Mapping[str, int],
) -> _SortKey:
    # Place / order from the least specific marked definition so an override
    # takes the original fixture's slot.
    origin = next(
        fixturedef
        for fixturedef in matched
        if _mark_info(fixturedef, info_type) is not None
    )
    stamp = getattr(origin.func, _MARKS_ORDER_ATTR)
    # Non-conftest plugins are not collection nodes (listchain has no entry
    # for them; baseid "" only coincides with Session.nodeid). Pytest puts
    # them before any located fixture.
    if not _fixture_has_location(origin):
        return _SortKey(has_location=False, site_rank=0, stamp=stamp)
    return _SortKey(
        has_location=True,
        site_rank=site_ranks[origin.baseid],
        stamp=stamp,
    )


def _definition_site_ranks(node: pytest.Item) -> dict[str, int]:
    return {
        ancestor.nodeid: index
        for index, ancestor in enumerate(node.listchain())
    }


def _fixture_has_location(fixturedef: pytest.FixtureDef[object]) -> bool:
    # pytest>=9 keeps the flag on _has_location; has_location warns / goes away.
    value = getattr(fixturedef, '_has_location', None)
    if value is not None:
        return bool(value)
    return bool(fixturedef.has_location)


def _mark_info(
    fixturedef: pytest.FixtureDef[object],
    info_type: type[I],
) -> I | None:
    marks = getattr(fixturedef.func, _MARKS_ATTR, None)
    if not marks:
        return None
    info = marks.get(info_type)
    if type(info) is info_type:
        return cast(I, info)
    return None
