import pytest

from testsuite.plugins import common


def test_when_loading_invalid_yaml_then_error_specifies_file(load_yaml):
    with pytest.raises(common.LoadYamlError) as err:
        load_yaml('invalid.yaml')
    assert 'invalid.yaml' in str(err)


def test_when_yaml_file_not_found_then_error_is_specific(load_yaml):
    with pytest.raises(FileNotFoundError) as err:
        load_yaml('non_existing.yaml')
    assert 'non_existing.yaml' in str(err)


def test_when_loading_invalid_json_then_error_specifies_file(load_json):
    with pytest.raises(common.LoadJsonError) as err:
        load_json('invalid.json')
    assert 'invalid.json' in str(err)


def test_when_json_file_not_found_then_error_is_specific(load_json):
    with pytest.raises(FileNotFoundError) as err:
        load_json('non_existing.json')
    assert 'non_existing.json' in str(err)
