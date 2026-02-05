import pathlib

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


def test_static(get_file_path, static_dir):
    assert get_file_path('case-local').relative_to(static_dir) == pathlib.Path(
        'test_common/test_static/case-local',
    )
    assert get_file_path('file-local').relative_to(static_dir) == pathlib.Path(
        'test_common/file-local',
    )
    assert get_file_path('default-local').relative_to(
        static_dir,
    ) == pathlib.Path('default/default-local')
    assert get_file_path('static-local').relative_to(
        static_dir,
    ) == pathlib.Path('static-local')


@pytest.mark.nofilldb
def test_search_path_custom(search_path_custom, static_dir):
    search_dirs = [
        static_dir / 'test_common',
        static_dir / 'default',
        static_dir,
    ]

    # Test finding file in multiple directories
    results = list(search_path_custom('file-local', search_dirs))
    assert len(results) == 1
    assert results[0].relative_to(static_dir) == pathlib.Path(
        'test_common/file-local',
    )

    # Test finding file that exists in multiple search directories
    results = list(search_path_custom('static-local', search_dirs))
    assert len(results) == 1
    assert results[0].relative_to(static_dir) == pathlib.Path('static-local')

    # Test with non-existent file (should return empty iterator)
    results = list(search_path_custom('does-not-exist', search_dirs))
    assert len(results) == 0


@pytest.mark.nofilldb
def test_search_path_custom_directory(search_path_custom, static_dir):
    results = list(
        search_path_custom('test_common', [static_dir], directory=True),
    )
    assert len(results) == 1
    assert results[0].is_dir()
    assert results[0].relative_to(static_dir) == pathlib.Path('test_common')


@pytest.mark.nofilldb
def test_get_path_custom(get_path_custom, static_dir):
    search_dirs = [
        static_dir / 'test_common',
        static_dir / 'default',
        static_dir,
    ]

    # Test finding file in first directory
    result = get_path_custom('file-local', search_dirs)
    assert result is not None
    assert result.relative_to(static_dir) == pathlib.Path(
        'test_common/file-local',
    )

    # Test finding file in later directory
    result = get_path_custom('default-local', search_dirs)
    assert result is not None
    assert result.relative_to(static_dir) == pathlib.Path(
        'default/default-local',
    )


@pytest.mark.nofilldb
def test_get_path_custom_missing_ok(get_path_custom, static_dir):
    search_dirs = [static_dir / 'test_common']

    result = get_path_custom(
        'does-not-exist',
        search_dirs,
        missing_ok=True,
    )
    assert result is None


@pytest.mark.nofilldb
def test_get_path_custom_missing_error(get_path_custom, static_dir):
    search_dirs = [static_dir / 'test_common']

    with pytest.raises(FileNotFoundError) as exc_info:
        get_path_custom('does-not-exist', search_dirs)

    assert 'does-not-exist' in str(exc_info.value)
    assert 'was not found' in str(exc_info.value)


@pytest.mark.nofilldb
def test_get_path_custom_directory(get_path_custom, static_dir):
    search_dirs = [static_dir]

    # Test finding directory
    result = get_path_custom('test_common', search_dirs, directory=True)
    assert result is not None
    assert result.is_dir()
    assert result.relative_to(static_dir) == pathlib.Path('test_common')

    # Test that file is not returned when directory=True
    result = get_path_custom(
        'static-local',
        search_dirs,
        directory=True,
        missing_ok=True,
    )
    assert result is None
