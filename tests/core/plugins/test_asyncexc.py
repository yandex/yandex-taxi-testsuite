import pytest

from testsuite.plugins import asyncexc


def test_check(asyncexc_append, asyncexc_check, _asyncexc):
    asyncexc_check()

    try:
        raise ValueError('oops')
    except ValueError as exc:
        asyncexc_append(exc)

    assert len(_asyncexc) == 1

    with pytest.raises(asyncexc.BackgroundExceptionError):
        asyncexc_check()

    assert len(_asyncexc) == 0

    asyncexc_check()
