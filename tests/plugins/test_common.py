import pytest

from testsuite._internal import fixture_types


@pytest.mark.nofilldb
def test_load(load: fixture_types.LoadFixture):
    data = load('test.txt')
    assert data == 'Hello, world!\n'


@pytest.mark.nofilldb
def test_load_binary_text(load_binary: fixture_types.LoadBinaryFixture):
    data = load_binary('test.txt')
    assert data == b'Hello, world!\n'


@pytest.mark.nofilldb
def test_load_notfound(load: fixture_types.LoadFixture):
    with pytest.raises(FileNotFoundError):
        load('does-not-exist')


@pytest.mark.nofilldb
def test_load_binary_bytes(load_binary: fixture_types.LoadBinaryFixture):
    data = load_binary('data.bin')
    assert data == b'\x88\x99\x100\x101\x1000'
