import pytest

from testsuite import fixture_markers

from ..visibility_marks import VisibilityMark, visibility


# Overrides the marked plugin fixture without repeating the mark.
@pytest.fixture(scope='session')
def plugin_visibility():
    return 'shadowed'


# A mark on the override replaces the inherited mark.
@pytest.fixture(scope='session')
@visibility('override')
def conftest_visibility():
    return 'replaced'


def test_unmarked_override_inherits_mark(request):
    infos = fixture_markers.get_infos(request, VisibilityMark)
    assert infos['plugin_visibility'].origin == 'plugin'


def test_marked_override_replaces_inherited_mark(request):
    infos = fixture_markers.get_infos(request, VisibilityMark)
    assert infos['conftest_visibility'].origin == 'override'
