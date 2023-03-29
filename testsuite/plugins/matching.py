import pytest

from testsuite.utils import matching


def _default_regex_match(doc: dict):
    return matching.RegexString(doc['pattern'])


def _default_partial_dict_match(doc: dict):
    return matching.PartialDict(doc['value'])


def pytest_register_matching_hooks():
    return {
        'any-value': matching.any_value,
        'any-float': matching.any_float,
        'any-integer': matching.any_integer,
        'any-numeric': matching.any_numeric,
        'positive-float': matching.positive_float,
        'positive-integer': matching.positive_integer,
        'positive-numeric': matching.positive_numeric,
        'negative-float': matching.negative_float,
        'negative-integer': matching.negative_integer,
        'negative-numeric': matching.negative_numeric,
        'non-negative-float': matching.non_negative_float,
        'non-negative-integer': matching.non_negative_integer,
        'non-negative-numeric': matching.non_negative_numeric,
        'any-string': matching.any_string,
        'uuid-string': matching.uuid_string,
        'objectid-string': matching.objectid_string,
        'datetime-string': matching.datetime_string,
        'regex': _default_regex_match,
        'partial-dict': _default_partial_dict_match,
    }


class Hookspec:
    def pytest_register_matching_hooks(self):
        pass


class MatchingPlugin:
    def __init__(self):
        self._matching_hooks = {}

    @property
    def matching_hooks(self):
        return self._matching_hooks

    def pytest_sessionstart(self, session):
        hooks = (
            session.config.pluginmanager.hook.pytest_register_matching_hooks()
        )
        for hook in hooks:
            self._matching_hooks.update(hook)

    def pytest_addhooks(self, pluginmanager):
        pluginmanager.add_hookspecs(Hookspec)


def pytest_configure(config):
    config.pluginmanager.register(MatchingPlugin(), 'matching_params')


@pytest.fixture(scope='session')
def operator_match(request, pytestconfig):
    plugin = pytestconfig.pluginmanager.get_plugin('matching_params')

    def _wrapper(doc: dict):
        for key, hook in plugin.matching_hooks.items():
            if doc['type'] == key:
                if callable(hook):
                    return hook(doc)
                return hook

        raise RuntimeError(f'Unknown match type {doc["type"]}')

    return _wrapper
