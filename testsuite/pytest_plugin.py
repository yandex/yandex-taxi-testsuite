# Common testsuite plugins
pytest_plugins = [
    'testsuite.plugins.loop',
    'testsuite.daemons.pytest_plugin',
    'testsuite.environment.pytest_plugin',
    'testsuite.logging.pytest_plugin',
    'testsuite.mockserver.pytest_plugin',
    'testsuite.plugins.assertrepr_compare',
    'testsuite.plugins.common',
    'testsuite.plugins.matching',
    'testsuite.plugins.mocked_time',
    'testsuite.plugins.network',
    'testsuite.plugins.object_hook',
    'testsuite.plugins.servicetest',
    'testsuite.plugins.tcp_mockserver',
    'testsuite.plugins.testpoint',
    'testsuite.plugins.verify_file_paths',
]
