import inspect
import re
import typing

import pytest

try:
    import annotationlib  # type: ignore

    def get_annotations(obj) -> dict:
        return annotationlib.get_annotations(obj)

    def get_namespace_annotations(dictionary) -> dict:
        func = annotationlib.get_annotate_from_class_namespace(dictionary)
        if func is None:
            return {}
        return func(annotationlib.Format.VALUE)

except ImportError:

    def get_annotations(obj) -> dict:
        return getattr(obj, '__annotations__', {})

    def get_namespace_annotations(dictionary) -> dict:
        return dictionary.get('__annotations__', {})


class FixtureMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        if bases:
            annotations = {}
            for base in bases:
                annotations.update(get_annotations(base))
            annotations.update(get_namespace_annotations(attrs))
            fixtures = {}
            fixture_types = {}
            for attr, attr_type in annotations.items():
                if attr.startswith('_fixture_'):
                    fixture = attr[9:]
                    fixtures[attr] = fixture
                    fixture_types[fixture] = attr_type
            attrs['__fixtures__'] = fixtures
            attrs['__fixture_types__'] = tuple(fixture_types.items())
        return super().__new__(mcs, name, bases, attrs)


class Fixture(metaclass=FixtureMetaclass):
    __fixtures__: dict[str, str]
    __fixture_types__: dict[str, typing.Any]

    def __init__(self, **kwargs):
        for attr, argname in self.__fixtures__.items():
            setattr(self, attr, kwargs[argname])

    def __repr__(self):
        args = ', '.join(self.__fixtures__.values())
        return f'<fixture {self.__class__.__name__}: args={args}>'


def create_fixture_factory(
    fixture_class,
    *,
    name: str | None = None,
    scope='function',
) -> typing.Callable:
    def factory(**kwargs):
        return fixture_class(**kwargs)

    if name is None:
        name = _classname_to_fixture(fixture_class.__name__)

    parameters = []
    # pylint: disable=protected-access
    for fixture_name, fixture_type in fixture_class.__fixture_types__:
        parameters.append(
            inspect.Parameter(
                name=fixture_name,
                annotation=fixture_type,
                kind=inspect.Parameter.KEYWORD_ONLY,
            ),
        )

    signature = inspect.signature(factory)
    factory.__signature__ = signature.replace(  # type: ignore
        parameters=parameters,
        return_annotation=fixture_class,
    )
    factory.__doc__ = fixture_class.__doc__
    factory.__name__ = name
    return pytest.fixture(scope=scope)(factory)


def _classname_to_fixture(string: str) -> str:
    if string.endswith('Fixture'):
        string = string[:-7]
    if not string:
        raise RuntimeError('Empty class name given')
    return (
        string[0].lower()
        + re.sub(
            r'[A-Z]',
            lambda matched: '_' + matched.group(0).lower(),  # type: ignore[operator]
            string[1:],
        )
    )
