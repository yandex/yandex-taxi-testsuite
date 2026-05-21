import pytest

from tests.core.conftest import KeyValue


def test_key_value_not_eq():
    left = KeyValue('somekey', 'somevalue')
    right = KeyValue('somekey', 'someothervalue')

    with pytest.raises(AssertionError) as key_value_exc:
        assert left == right

    with pytest.raises(AssertionError) as dict_exc:
        assert left.to_dict() == right.to_dict()

    assert str(key_value_exc.value) == str(dict_exc.value)
