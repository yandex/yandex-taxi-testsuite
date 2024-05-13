import pytest

from testsuite.plugins import network


@pytest.mark.nofilldb
@pytest.mark.parametrize(
    'method', ['get_free_port', '_get_free_port_range_based']
)
def test_get_free_port(request, method):
    get_free_port = request.getfixturevalue(method)

    max_ports = 10
    ports = set()
    for _ in range(max_ports):
        ports.add(get_free_port())
    assert len(ports) == max_ports
