import pytest

from testsuite.environment import main


def test_noargs():
    with pytest.raises(SystemExit) as exc:
        main.main(args=[])

    assert exc.value.code == 2


def test_start(monkeypatch):
    calls = []

    def command_start(env, args):
        calls.append(1)

    monkeypatch.setattr(main, '_command_start', command_start)
    main.main(args=['start'])
    assert calls
