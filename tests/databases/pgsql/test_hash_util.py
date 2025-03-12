import pathlib

import pytest

from testsuite.databases.pgsql import utils


@pytest.mark.parametrize('hash_directory', [(True,), (False,)])
def test_hash_changes_with_file_content(temp_dir_path, hash_directory: bool):
    file = temp_dir_path.joinpath('file')
    hash_source = (temp_dir_path,) if hash_directory else (file,)

    with file.open('wb') as stream:
        stream.write(b'abc')
    hash_original = utils.get_files_hash(hash_source)

    with file.open('wb') as stream:
        stream.write(b'abcd')
    hash_modified = utils.get_files_hash(hash_source)
    assert hash_original != hash_modified

    with file.open('wb') as stream:
        stream.write(b'abc')
    hash_original2 = utils.get_files_hash(hash_source)
    assert hash_original2 == hash_original


def test_hash_changes_with_file_name(temp_dir_path):
    original_file = temp_dir_path.joinpath('file1')
    renamed_file = temp_dir_path.joinpath('file2')
    hash_source = (temp_dir_path,)
    with original_file.open('wb') as stream:
        stream.write(b'')

    hash_original = utils.get_files_hash(hash_source)

    original_file.rename(renamed_file)
    hash_modified = utils.get_files_hash(hash_source)
    assert hash_original != hash_modified

    renamed_file.rename(original_file)
    hash_original2 = utils.get_files_hash(hash_source)
    assert hash_original2 == hash_original


@pytest.fixture
def temp_dir_path(testdir):
    return pathlib.Path(testdir.tmpdir.strpath)
