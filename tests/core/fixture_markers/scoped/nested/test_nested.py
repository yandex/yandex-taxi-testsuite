from visibility_marks import VisibilityMark

from testsuite import fixture_markers


def test_nested_sees_parent_and_own_conftest(request):
    infos = fixture_markers.get_infos(request, VisibilityMark)
    assert infos['plugin_visibility'].origin == 'plugin'
    assert infos['conftest_visibility'].origin == 'conftest'
    assert infos['nested_conftest_visibility'].origin == 'nested-conftest'
    assert 'module_visibility' not in infos
    assert 'unrelated_module_visibility' not in infos
    assert 'function_visibility' not in infos
