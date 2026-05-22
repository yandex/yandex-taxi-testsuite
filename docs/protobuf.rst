Protobuf
========

Testsuite provides matchers and utilities for working with protobuf messages in
tests. To use them, install the ``protobuf`` extra:

.. code-block:: bash

   pip install yandex-taxi-testsuite[protobuf]

Enable the plugin by adding it to ``pytest_plugins`` in your ``conftest.py``:

.. code-block:: python

   pytest_plugins = [
       'testsuite.pytest_plugin',
       'testsuite.protobuf.pytest_plugin',
   ]

The plugin registers compare visitors so that when two protobuf messages (or a
message and a matcher) are compared with ``assert``, the failure output shows
human-readable field diffs rather than raw byte strings.

Matchers
--------

``ProtobufDict``
~~~~~~~~~~~~~~~~

Compares a protobuf message against a plain dict. The message is converted to a
dict via :func:`testsuite.protobuf.utils.message_to_dict` (which uses
``preserving_proto_field_name=True``) before the comparison.

.. code-block:: python

   from testsuite.protobuf.matching import ProtobufDict

   def test_response(my_proto_message):
       assert my_proto_message == ProtobufDict({'field': 'value', 'count': 1})

``PartialProtobufDict``
~~~~~~~~~~~~~~~~~~~~~~~

Like ``ProtobufDict``, but only checks the keys present in the expected dict —
extra fields in the actual message are ignored.

.. code-block:: python

   from testsuite.protobuf.matching import PartialProtobufDict

   def test_response(my_proto_message):
       # passes as long as 'field' == 'value', ignores other fields
       assert my_proto_message == PartialProtobufDict({'field': 'value'})

Classes
-------

.. currentmodule:: testsuite.protobuf.matching

.. autoclass:: ProtobufDict
   :members:

.. autoclass:: PartialProtobufDict
   :members:

Utilities
---------

.. currentmodule:: testsuite.protobuf.utils

.. autofunction:: message_to_dict
