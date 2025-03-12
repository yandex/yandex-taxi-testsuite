from testsuite import matching


def test_any():
    assert matching.any_value == object()
    assert matching.any_value == 123
    assert matching.any_value == 'foo'


def test_self():
    assert matching.any_value == matching.any_value
    assert matching.Any() == matching.Any()
