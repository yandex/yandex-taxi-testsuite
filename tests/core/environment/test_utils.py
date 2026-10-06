import pytest

from testsuite.environment import utils


def test_getenv_port_default(monkeypatch):
    monkeypatch.delenv('TESTSUITE_TEST_PORT', raising=False)
    assert utils.getenv_port(key='TESTSUITE_TEST_PORT', default=1234) == 1234


def test_getenv_port_explicit(monkeypatch):
    monkeypatch.setenv('TESTSUITE_TEST_PORT', '4321')
    assert utils.getenv_port(key='TESTSUITE_TEST_PORT', default=1234) == 4321


def test_getenv_port_invalid(monkeypatch):
    monkeypatch.setenv('TESTSUITE_TEST_PORT', 'foobar')
    with pytest.raises(utils.EnvironmentVariableError):
        utils.getenv_port(key='TESTSUITE_TEST_PORT', default=1234)


def test_getenv_port_auto(monkeypatch):
    monkeypatch.setenv('TESTSUITE_TEST_PORT_AUTO', 'auto')
    port = utils.getenv_port(key='TESTSUITE_TEST_PORT_AUTO', default=1234)
    assert 0 < port < 65536
    assert port != 1234
    assert (
        utils.getenv_port(key='TESTSUITE_TEST_PORT_AUTO', default=1234) == port
    )


def test_getenv_port_auto_per_key(monkeypatch):
    monkeypatch.setenv('TESTSUITE_TEST_PORT_AUTO_A', 'auto')
    monkeypatch.setenv('TESTSUITE_TEST_PORT_AUTO_B', 'auto')
    port_a = utils.getenv_port(key='TESTSUITE_TEST_PORT_AUTO_A', default=1234)
    port_b = utils.getenv_port(key='TESTSUITE_TEST_PORT_AUTO_B', default=1234)
    assert port_a != port_b
