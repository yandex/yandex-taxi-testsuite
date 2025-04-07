from testsuite._internal import compare_transform


def test_build_path():
    assert compare_transform._build_path(['foo', '["bar"]']) == 'foo["bar"]'
    assert compare_transform._build_path(['foo'], '["bar"]') == 'foo["bar"]'
    assert compare_transform._build_path(['foo'], ('["bar"]',)) == 'foo["bar"]'
    assert compare_transform._build_path(['foo'], ['["bar"]']) == 'foo["bar"]'
