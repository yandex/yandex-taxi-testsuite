from unittest import mock

import pytest

from testsuite.databases.mysql import pytest_plugin


@pytest.mark.parametrize('explicit_port', [None, 23456])
def test_service_settings_port(monkeypatch, explicit_port):
    if explicit_port is None:
        monkeypatch.delenv('TESTSUITE_MYSQL_PORT', raising=False)
    else:
        monkeypatch.setenv('TESTSUITE_MYSQL_PORT', str(explicit_port))

    request = mock.Mock()
    if explicit_port is None:
        request.getfixturevalue.return_value = lambda: 12345
    else:
        request.getfixturevalue.side_effect = AssertionError(
            'An explicit port must not request the port allocator',
        )

    settings = pytest_plugin.mysql_service_settings.__wrapped__(request)
    assert settings.port == (explicit_port or 12345)


def test_connection_matches_local_settings(pytestconfig, request):
    if pytestconfig.option.mysql:
        pytest.skip('This test checks the local server settings')
    settings = request.getfixturevalue('mysql_service_settings')
    conninfo = request.getfixturevalue('mysql_conninfo')
    assert conninfo == settings.get_conninfo()


@pytest.mark.parametrize('scenario', ['external', 'disabled', 'no-databases'])
def test_no_local_settings(pytester, scenario):
    databases = '{}' if scenario == 'no-databases' else "{'testdb': object()}"
    pytester.makeconftest(
        """
        import pytest

        pytest_plugins = [
            'testsuite.pytest_plugin',
            'testsuite.databases.mysql.pytest_plugin',
        ]

        @pytest.fixture(scope='session')
        def _mysql_service_settings():
            raise AssertionError('Local settings must not be requested')

        @pytest.fixture
        def ensure_service_started():
            raise AssertionError('Local launcher must not be requested')

        @pytest.fixture(scope='session')
        def mysql_local():
            return DATABASES
    """.replace('DATABASES', databases)
    )
    pytester.makepyfile(
        """
        def test_no_local_server(request):
            expected = SCENARIO == 'external'
            assert request.getfixturevalue('_mysql_service') is expected
            if expected:
                conninfo = request.getfixturevalue('mysql_conninfo')
                assert conninfo.hostname == 'external-db'
                assert conninfo.port == 3307
                assert conninfo.user == 'user'
                assert conninfo.password == 'password'
    """.replace('SCENARIO', repr(scenario))
    )
    args = []
    if scenario == 'external':
        args.append('--mysql=mysql://user:password@external-db:3307')
    elif scenario == 'disabled':
        args.append('--no-mysql')
    result = pytester.runpytest_subprocess(*args)
    result.assert_outcomes(passed=1)


@pytest.mark.parametrize(
    'fixture_name',
    ['mysql_service_settings', '_mysql_service_settings'],
)
def test_settings_override_is_shared_with_launcher(pytester, fixture_name):
    pytester.makeconftest(
        """
        import pytest
        from testsuite.databases.mysql.classes import ServiceSettings

        pytest_plugins = [
            'testsuite.pytest_plugin',
            'testsuite.databases.mysql.pytest_plugin',
        ]

        @pytest.fixture(scope='session')
        def FIXTURE_NAME():
            return ServiceSettings(port=23456)

        @pytest.fixture(scope='session')
        def mysql_local():
            return {'testdb': object()}

        @pytest.fixture
        def ensure_service_started(mysql_conninfo):
            def start(name, *, settings):
                assert name == 'mysql'
                assert settings.get_conninfo() == mysql_conninfo
            return start
    """.replace('FIXTURE_NAME', fixture_name)
    )
    pytester.makepyfile("""
        def test_local_server(_mysql_service, mysql_conninfo):
            assert _mysql_service is True
            assert mysql_conninfo.port == 23456
    """)
    result = pytester.runpytest_subprocess()
    result.assert_outcomes(passed=1)
