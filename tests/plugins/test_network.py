import pytest

from testsuite.plugins import network


@pytest.mark.nofilldb
def test_get_free_port_error(get_free_port):
    max_ports = 101

    ports = set()
    for _ in range(max_ports):
        ports.add(get_free_port())
    assert len(ports) == max_ports, 'get_free_port() returns duplicate ports'
