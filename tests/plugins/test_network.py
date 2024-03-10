import pytest

from testsuite.plugins import network


@pytest.mark.nofilldb
def test_get_free_port_error(get_free_port):
    ports = set()
    for _ in range(MAX_PORTS_NUMBER):
        ports.add(get_free_port())
    assert len(ports) == MAX_PORTS_NUMBER
