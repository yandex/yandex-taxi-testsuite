Chat backend example
====================

.. contents::
   :depth: 2
   :local:

Task of storing messages is delegated to an external service

Chat backend service
~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: server.py

Conftest
~~~~~~~~

.. literalinclude:: tests/conftest.py


Test
~~~~

.. literalinclude:: tests/test_service.py
