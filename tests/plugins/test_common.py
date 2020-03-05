import pytest

from testsuite.plugins import common


@pytest.mark.nofilldb
def test_load(load):
    data = load('test.txt')
    assert data == 'Hello, world!\n'


@pytest.mark.nofilldb
def test_load_binary_text(load_binary):
    data = load_binary('test.txt')
    assert data == b'Hello, world!\n'


@pytest.mark.nofilldb
def test_load_notfound(load):
    with pytest.raises(FileNotFoundError):
        load('does-not-exist')


@pytest.mark.nofilldb
def test_load_binary_bytes(load_binary):
    data = load_binary('data.bin')
    assert data == b'\x88\x99\x100\x101\x1000'


@pytest.mark.nofilldb
def test_get_free_port_error(get_free_port):
    with pytest.raises(common.NoEnabledPorts):
        for _ in range(common.MAX_PORTS_NUMBER + 1):
            get_free_port()
