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
