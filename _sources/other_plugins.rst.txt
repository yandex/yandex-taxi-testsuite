Other plugins
=============

.. _OtherPlugins:

Envinfo
-------

Envinfo plugin adds some details to test report header ::

   args: python3 -m pytest -vv -x
   hostname: machine-hostname
   git: branch current_branch, commit_hash*, base base_commit_hash

In ``git:`` section

* ``*`` indicates uncommitted changes
* ``base_commit_hash`` points to a commit in ``develop`` branch from which the
  current branch diverges

To use envinfo plugin, add it to ``pytest_plugins`` in ``conftest.py``

.. code-block:: python

   pytest_plugins = [
       # ...
       'testsuite.envinfo',
   ]

Retrieving git status can be slow in docker due to network-related issues.
If it affects you, turn git status off by ``--envinfo-no-git`` flag.

Mocked_time
-----------
.. currentmodule:: testsuite.plugins.mocked_time

Fixtures
~~~~~~~~

.. autofunction:: mocked_time()
   :no-auto-options:

``mocked_time`` fixture provides control over mock time in a centralized way.

Disabling mocked_time
~~~~~~~~~~~~~~~~~~~~~

- ``mocked-time-enabled = false`` flag in ``pytest.ini`` disables mocked time
  by default.
- ``--service-runner-mode`` command line flag disables mocked time by default.

When mocked time is disabled by default, it has to explicitly enabled to be
used in a particular test: ``@pytest.mark.now('2016-12-01T12:00:00')`` or
``@pytest.mark.now(enabled=True)``.

If time is not specified in ``@pytest.mark.now``, then
``datetime.datetime.utcnow()`` value at the start of test is used as time value
until it is modified by calling ``mocked_time.set(...)`` or
``mocked_time.sleep(...)``

Classes
~~~~~~~

.. autoclass:: MockedTime
    :members: now, set, sleep
