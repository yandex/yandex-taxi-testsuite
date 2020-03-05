Utils
=====

.. _AsyncCallQueue:

AsyncCallQueue
--------------

.. currentmodule:: testsuite.utils.callinfo

Async callqueue wrapper. Stores information about each function call to
synchronized queue.

.. code-block:: python

    @callinfo.acallqueue
    async def func(a, b):
        return a + b

    await func(1, 2)

    >>> func.has_calls
    True
    >>> func.times_called
    1
    >>> func.next_call()
    {'a': 1, 'b': 2}


.. autoclass:: AsyncCallQueue
    :members:
.. autofunction:: acallqueue


Envinfo
-------

Envinfo plugin adds following information to test report header ::

   args: python3.7 -m pytest -vv -x
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
