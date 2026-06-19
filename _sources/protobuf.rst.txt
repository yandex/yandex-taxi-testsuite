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

All matchers are imported from ``testsuite.protobuf.matching`` and convert the
actual protobuf message to a dict via
:func:`testsuite.protobuf.utils.message_to_dict` (which uses
``preserving_proto_field_name=True``) before comparing it against the expected
dict.

.. currentmodule:: testsuite.protobuf.matching

.. autoclass:: ProtobufDict
   :members:

.. autoclass:: PartialProtobufDict
   :members:

.. autoclass:: RecursivePartialProtobufDict
   :members:

Utilities
---------

.. currentmodule:: testsuite.protobuf.utils

.. autofunction:: message_to_dict
