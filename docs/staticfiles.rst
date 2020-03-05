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

.. autofunction:: load(path)
   :no-auto-options:

load_binary
~~~~~~~~~~~

.. autofunction:: load_binary(path)
   :no-auto-options:


load_json
~~~~~~~~~

.. autofunction:: load_json(path, *args, **kwargs)
   :no-auto-options:


load_yaml
~~~~~~~~~

.. autofunction:: load_yaml(path)
   :no-auto-options:
