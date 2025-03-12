from testsuite.utils import matching


def test_legacy_module():
    assert 'foo' == matching.any_string
