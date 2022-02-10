.. _staticfiles:

Working with static files
=========================

.. currentmodule:: testsuite.plugins.common

Testsuite provides functions to work with static files associated with
testscase. It searches for files in static directoy relative to the current
file.
If your tests is located in ``tests/test_service.py`` testsuite will search for
the static file ``foo.txt`` in the following directories:

* test case local: ``tests/static/test_services/test_case_name/foo.txt``
* test file local: ``tests/static/test_services/foo.txt``
* test package local: ``tests/static/default/foo.txt``

``FileNotFoundError`` would be raised if no file is found.

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
