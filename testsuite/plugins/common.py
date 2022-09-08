import json
import pathlib
import typing
import warnings

import pytest

from testsuite import annotations
from testsuite._internal import fixture_class
from testsuite.utils import json_util
from testsuite.utils import yaml_util


class BaseError(Exception):
    """Base class for errors from this module."""


class UnsupportedFileModeError(BaseError):
    """Unsupported file open mode passed."""


class LoadJsonError(BaseError):
    """Json file load or parse failure error."""


class LoadYamlError(BaseError):
    """Yaml file load or parse failure error."""


class GetSearchPathesFixture(fixture_class.Fixture):
    """Generates sequence of pathes for static files."""

    _fixture__search_directories: typing.Tuple[str, ...]

    def __call__(
            self, filename: annotations.PathOrStr,
    ) -> typing.Iterator[pathlib.Path]:
        for directory in self._fixture__search_directories:
            yield pathlib.Path(directory) / filename


class SearchPathFixture(fixture_class.Fixture):
    _fixture_get_search_pathes: GetSearchPathesFixture

    def __call__(
            self, filename: annotations.PathOrStr, directory: bool = False,
    ) -> typing.Iterator[pathlib.Path]:
        for abs_filename in self._fixture_get_search_pathes(filename):
            if directory:
                if abs_filename.is_dir():
                    yield abs_filename
            else:
                if abs_filename.is_file():
                    yield abs_filename


class GetFilePathFixture(fixture_class.Fixture):
    """Returns path to static regular file."""

    _fixture_search_path: SearchPathFixture
    _fixture_get_search_pathes: GetSearchPathesFixture

    def __call__(self, filename: annotations.PathOrStr) -> pathlib.Path:
        for path in self._fixture_search_path(filename):
            return path
        raise self._file_not_found_error(
            f'File {filename} was not found', filename,
        )

    def _file_not_found_error(self, message, filename):
        pathes = '\n'.join(
            ' - %s' % path
            for path in self._fixture_get_search_pathes(filename)
        )
        return FileNotFoundError(
            '%s\n\nThe following pathes were examined:\n%s'
            % (message, pathes),
        )


class GetDirectoryPathFixture(GetFilePathFixture):
    """Returns path to static directory."""

    def __call__(self, filename: annotations.PathOrStr) -> pathlib.Path:
        for path in self._fixture_search_path(filename, directory=True):
            return path
        raise self._file_not_found_error(
            f'Directory {filename} was not found', filename,
        )


class OpenFileFixture(fixture_class.Fixture):
    """Open static file by name.

    Only read-only open modes are supported.

    Example:

    .. code-block:: python

        def test_foo(open_file):
            with open_file('foo') as fp:
                ...
    """

    _modes_whitelist = frozenset(['r', 'rt', 'rb'])

    _fixture_get_file_path: GetFilePathFixture

    def __call__(
            self,
            filename: annotations.PathOrStr,
            mode='r',
            buffering=-1,
            encoding='utf-8',
            errors=None,
    ) -> typing.IO:
        if mode not in self._modes_whitelist:
            raise UnsupportedFileModeError(
                f'Incorrect file open mode {mode!r} passed. '
                f'Only read-only modes are supported.',
            )
        return open(
            self._fixture_get_file_path(filename),
            mode=mode,
            buffering=buffering,
            encoding=encoding,
            errors=errors,
        )


class LoadFixture(fixture_class.Fixture):
    """Load file from static directory.

    Example:

    .. code-block:: python

        def test_something(load):
            data = load('filename')

    :return: :py:class:`LoadFixture` callable instance.
    """

    _fixture_open_file: OpenFileFixture

    def __call__(
            self,
            filename: annotations.PathOrStr,
            mode='r',
            encoding='utf-8',
            errors=None,
    ) -> typing.Union[bytes, str]:
        """Load static text file.

        :param filename: static file name part.
        :param mode: file open mode, see :func:`open`, read-only modes are
            supported.
        :param encoding: stream encoding, see :func:`open`.
        :param errors: error handling mode see :func:`open`.
        :returns: ``str`` instance. Binary mode is obsolte, use
          :func:`load_binary` fixture instead.
        """
        if 'b' in mode:
            warnings.warn(
                'load(): binary mode is deprecated, use load_binary() instead',
                PendingDeprecationWarning,
            )
        with self._fixture_open_file(
                filename, mode=mode, encoding=encoding, errors=errors,
        ) as file:
            return file.read()


class LoadBinaryFixture(fixture_class.Fixture):
    """Load binary data from static directory.

    Example:

    .. code-block:: python

        def test_something(load_binary):
            bytes_data = load_binary('data.bin')
    """

    _fixture_open_file: OpenFileFixture

    def __call__(self, filename: annotations.PathOrStr) -> bytes:
        """Load static binary file.

        :param filename": static file name part
        :returns: ``bytes`` file content.
        """
        with self._fixture_open_file(
                filename, mode='rb', encoding=None,
        ) as file:
            return file.read()


class JsonLoadsFixture(fixture_class.Fixture):
    """Load json doc from string.

    Json loader runs ``json_util.loads(data, ..., *args, **kwargs)`` hooks.
    It does:
    * bson.json_util.object_hook()
    * mockserver substitution

    Example:

    .. code-block:: python

        def test_something(json_loads):
            json_obj = json_loads('{"key": "value"}')
    """

    _fixture_load_json_defaults: typing.Dict
    _fixture_object_hook: typing.Any

    def __call__(self, content, *args, **kwargs) -> typing.Any:
        if 'object_hook' not in kwargs:
            kwargs['object_hook'] = self._fixture_object_hook
        return json_util.loads(
            content, *args, **self._fixture_load_json_defaults, **kwargs,
        )


class LoadJsonFixture(fixture_class.Fixture):
    """Load json doc from static directory.

    Json loader runs ``json_util.loads(data, ..., *args, **kwargs)`` hooks.
    It does:
    * bson.json_util.object_hook()
    * mockserver substitution

    Example:

    .. code-block:: python

        def test_something(load_json):
            json_obj = load_json('filename.json')
    """

    _fixture_load: LoadFixture
    _fixture_json_loads: JsonLoadsFixture

    def __call__(
            self, filename: annotations.PathOrStr, *args, **kwargs,
    ) -> typing.Any:
        content = self._fixture_load(filename)
        try:
            return self._fixture_json_loads(content, *args, **kwargs)
        except json.JSONDecodeError as err:
            raise LoadJsonError(
                f'Failed to load JSON file {filename}',
            ) from err


class LoadYamlFixture(fixture_class.Fixture):
    """Load yaml doc from static directory.

    .. code-block:: python

        def test_something(load_yaml):
            yaml_obj = load_yaml('filename.yaml')
    """

    _fixture_load: LoadFixture

    def __call__(
            self, filename: annotations.PathOrStr, *args, **kwargs,
    ) -> typing.Any:
        content = self._fixture_load(filename)
        try:
            return yaml_util.load(content, *args, **kwargs)
        except yaml_util.ParserError as exc:
            raise LoadYamlError(
                f'Failed to load YAML file {filename}',
            ) from exc


FilePathsCache = typing.Dict[pathlib.Path, typing.List[pathlib.Path]]

get_search_pathes = fixture_class.create_fixture_factory(
    GetSearchPathesFixture,
)
search_path = fixture_class.create_fixture_factory(SearchPathFixture)
get_file_path = fixture_class.create_fixture_factory(GetFilePathFixture)
get_directory_path = fixture_class.create_fixture_factory(
    GetDirectoryPathFixture,
)
open_file = fixture_class.create_fixture_factory(OpenFileFixture)
load = fixture_class.create_fixture_factory(LoadFixture)
load_binary = fixture_class.create_fixture_factory(LoadBinaryFixture)
json_loads = fixture_class.create_fixture_factory(JsonLoadsFixture)
load_json = fixture_class.create_fixture_factory(LoadJsonFixture)
load_yaml = fixture_class.create_fixture_factory(LoadYamlFixture)


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'nofilldb: test does not need db initialization',
    )


@pytest.fixture
def static_dir(testsuite_request_directory) -> pathlib.Path:
    """Static directory related to test path.

    Returns static directory relative to test file, e.g.::

       |- tests/
          |- static/ <-- base static directory for test_foo.py
          |- test_foo.py

    """
    return testsuite_request_directory / 'static'


@pytest.fixture
def initial_data_path() -> typing.Tuple[pathlib.Path, ...]:
    """Use this fixture to override base static search path.

    .. code-block:: python

     @pytest.fixture
     def initial_data_path():
         return (
             pathlib.Path(PROJECT_ROOT) / 'tests/static',
             pathlib.Path(PROJECT_ROOT) / 'static',
         )
    """

    return ()


@pytest.fixture
def get_all_static_file_paths(
        static_dir: pathlib.Path, _file_paths_cache: FilePathsCache,
):
    def _get_file_paths() -> typing.List[pathlib.Path]:
        if static_dir not in _file_paths_cache:
            _file_paths_cache[static_dir] = [
                path for path in static_dir.rglob('') if path.is_file
            ]
        return _file_paths_cache[static_dir]

    return _get_file_paths


@pytest.fixture
def object_substitute(object_hook):
    """Perform object substitution as in load_json."""

    def _substitute(content, *args, **kwargs):
        return json_util.substitute(
            content, object_hook=object_hook, *args, **kwargs,
        )

    return _substitute


@pytest.fixture(scope='session')
def testsuite_get_source_path():
    def get_source_path(path) -> pathlib.Path:
        return pathlib.Path(path)

    return get_source_path


@pytest.fixture(scope='session')
def testsuite_get_source_directory(testsuite_get_source_path):
    def get_source_directory(path) -> pathlib.Path:
        return testsuite_get_source_path(path).parent

    return get_source_directory


@pytest.fixture
def testsuite_request_path(request, testsuite_get_source_path) -> pathlib.Path:
    return testsuite_get_source_path(request.module.__file__)


@pytest.fixture
def testsuite_request_directory(testsuite_request_path) -> pathlib.Path:
    return testsuite_request_path.parent


@pytest.fixture(scope='session')
def worker_id(request) -> str:
    if hasattr(request.config, 'workerinput'):
        return request.config.workerinput['workerid']
    return 'master'


@pytest.fixture(scope='session')
def _file_paths_cache() -> FilePathsCache:
    return {}


@pytest.fixture
def _search_directories(
        request,
        static_dir: pathlib.Path,
        initial_data_path: typing.Tuple[pathlib.Path, ...],
        testsuite_request_path,
) -> typing.Tuple[pathlib.Path, ...]:
    test_module_name = pathlib.Path(testsuite_request_path.stem)
    node_name = request.node.name
    if '[' in node_name:
        node_name = node_name[: node_name.index('[')]
    local_path = [test_module_name / node_name]
    local_path.append(test_module_name)
    local_path.append('default')
    local_path.append('')
    search_directories = [static_dir / subdir for subdir in local_path]
    search_directories.extend(initial_data_path)
    return tuple(search_directories)


@pytest.fixture(scope='session')
def load_json_defaults():
    return {}
