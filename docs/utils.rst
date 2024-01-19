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


Matching
========

.. currentmodule:: testsuite.utils.matching

Testsuite provides utility to perform inexact pattern matching.
This might be useful when comparing objects.
For instance when checking HTTP handle response.
Special objects with custom `__eq__()` method are used for pattern matching.
You can use them instead of explicit value when comparing objects.

Here is example assertion on `order/create` handle response when you do not need to know exact order id returned by handle.


.. code-block:: python

   from testsuite.utils import matching

   def test_order_create(...):
       response = await client.post('/order/create')
       assert response.status_code == 200

       assert response.json() == {
           'order_id': matching.uuid_string,
           ...
       }

String matching
---------------

Regular expressions
~~~~~~~~~~~~~~~~~~~

.. autoclass:: RegexString


Predicates
~~~~~~~~~~

* ``any_string``, matches any string
* ``datetime_string``, matches any datetime string using `dateutil.parser`
* ``uuid_string``, string is uuid, e.g.: d08535a5904f4790bd8f95c51c1f3cbe
* ``objectid_string``, String is Mongo objectid, e.g 5e64beab56d0bf70bd8eebcb

Integer matching
----------------

Gt
~~

.. autoclass:: Gt

Ge
~~

.. autoclass:: Ge


Lt
~~

.. autoclass:: Lt

Le
~~

.. autoclass:: Le

Predicates
~~~~~~~~~~

* ``any_float``
* ``any_integer``
* ``any_numeric``
* ``positive_float``
* ``positive_integer``
* ``positive_numeric``
* ``negative_float``
* ``negative_integer``
* ``negative_numeric``
* ``non_negative_float``
* ``non_negative_integer``
* ``non_negative_numeric``

Type matching
-------------

.. autoclass:: IsInstance

Logical matching
----------------

And
~~~

.. autoclass:: And

Or
~~

.. autoclass:: Or

Not
~~~

.. autoclass:: Not

Partial dict
------------

.. autoclass:: PartialDict


Unordered list
--------------

.. autofunction:: unordered_list
