import pytest

from testsuite.plugins import network


@pytest.mark.nofilldb
def test_get_free_port_error(get_free_port):
    with pytest.raises(network.NoEnabledPorts):
        for _ in range(network.MAX_PORTS_NUMBER + 1):
            get_free_port()
