import sys
from pathlib import Path

_DIR = str(Path(__file__).parent)
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from visibility_marks import VisibilityPlugin


def pytest_configure(config):
    if config.pluginmanager.has_plugin('visibility_plugin'):
        return
    config.pluginmanager.register(VisibilityPlugin(), 'visibility_plugin')
