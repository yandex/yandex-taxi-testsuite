import pytest

pytest.importorskip('google.protobuf')

pytest_plugins = [
    'tests.core.plugins.protobuf.envelope_plugin',
    'testsuite.protobuf.pytest_plugin',
]
