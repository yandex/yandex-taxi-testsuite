Docker integration example
==========================

Dockerfile
----------

First of all you need to build an image with testsuite, here is example
Dockerfile:

.. literalinclude:: testsuite/Dockerfile


docker-compose.yaml
-------------------

Then you need to configure docker-compose to start required enironment and run
testsuite:

.. literalinclude:: testsuite/Dockerfile
