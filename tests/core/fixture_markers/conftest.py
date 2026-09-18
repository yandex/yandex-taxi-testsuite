from .visibility_marks import VisibilityPlugin


def pytest_configure(config):
    if config.pluginmanager.has_plugin('visibility_plugin'):
        return
    config.pluginmanager.register(VisibilityPlugin(), 'visibility_plugin')
