.. _staticfiles:

Working with static files
=========================

.. currentmodule:: testsuite.plugins.common

Testsuite provides functions to work with static files associated with
testscase. It searches for files in static directoy relative to the current
file.
If your tests is located in ``tests/test_foo.py`` testsuite will search for
the static file ``filename.txt`` in the following order:

.. list-table:: Static file lookup order
   :header-rows: 1

   * - Name
     - Example path
   * - Per case
     - ``tests/static/test_foo/test_case_name/filename.txt``
   * - Per file
     - ``tests/static/test_foo/filename.txt``
   * - Per package `default/`
     - ``tests/static/default/filename.txt``
   * - Static directory
     - ``tests/static/filename.txt``
   * - Initial data dirs
     - see :func:`initial_data_path()`
   * - Not found
     - ``FileNotFoundError`` would be raised

Fixtures
--------

load
~~~~

.. py:function:: load

   Returns :py:class:`LoadFixture` instance.

.. autoclass:: LoadFixture()
    :members: __call__

load_binary
~~~~~~~~~~~

.. py:function:: load_binary

   Returns :py:class:`LoadBinaryFixture` instance.

.. autoclass:: LoadBinaryFixture()
    :members: __call__

load_json
~~~~~~~~~

.. py:function:: load_json

   Returns :py:class:`LoadJsonFixture` instance.

.. autoclass:: LoadJsonFixture()
    :members: __call__


load_yaml
~~~~~~~~~

.. py:function:: load_yaml

   Returns :py:class:`LoadYamlFixture` instance.

.. autoclass:: LoadYamlFixture()
    :members: __call__


open_file
~~~~~~~~~

.. py:function:: open_file

   Returns :py:class:`OpenFileFixture` instance.

.. autoclass:: OpenFileFixture()
    :members: __call__


get_file_path
~~~~~~~~~~~~~

.. py:function:: get_file_path

   Returns :py:class:`GetFilePathFixture` instance.

.. autoclass:: GetFilePathFixture()
    :members: __call__


get_directory_path
~~~~~~~~~~~~~~~~~~

.. py:function:: get_directory_path

   Returns :py:class:`GetDirectoryPathFixture` instance.

.. autoclass:: GetDirectoryPathFixture()
    :members: __call__


get_search_pathes
~~~~~~~~~~~~~~~~~

.. py:function:: get_search_pathes

   Returns :py:class:`GetSearchPathesFixture` instance.

.. autoclass:: GetSearchPathesFixture()
    :members: __call__

static_dir
~~~~~~~~~~

.. autofunction:: static_dir


initial_data_path
~~~~~~~~~~~~~~~~~

.. autofunction:: initial_data_path


testsuite_get_source_path
~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: testsuite_get_source_path(path) -> pathlib.Path

   Returns source path related to given `path`.

   .. code-block:: python

       def test_foo(testsuite_get_source_path):
           path = testsuite_get_source_path(__file__)
           ...


testsuite_get_source_directory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. py:function:: testsuite_get_source_directory(path) -> pathlib.Path

   Session scope fixture. Returns source directory related to given `path`.

   This fixture can be used to access data files in session fixtures, e.g::

       |- tests/
          |- test_foo.py
          |- foo.txt


   .. code-block:: python

       @pytest.fixture(scope='session')
       def my_data(get_source_directory):
           return (
               testsuite_get_source_directory(__file__)
               .joinpath('foo.txt')
               .read_text()
           )
