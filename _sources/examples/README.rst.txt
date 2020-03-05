Examples
========
Here we demonstrate how to use testsuite based on a simple chat application.

The frontend (``chat-backend/chat.html``) interacts with ``chat-backend``, a
simple HTTP service written in Python. ``chat-backend`` then communicates to an
external storage service to actually store chat messages.

Two alternative storage services are implemented:

* ``chat-storage-postgres`` - stores chat messages in PostgreSQL database
* ``chat-storage-mongo`` - stores chat messages in MongoDB database

Directory structure ::

   chat-xxx/server.py - simple microservice written in python
   chat-xxx/tests     - testsuite tests

Running examples
----------------

You can run tests using system pytest.

Run tests for all examples ::

   make runtests

Run tests for a particular example ::

   make runtests-chat-backend
   make runtests-chat-storage-postgres
   make runtests-chat-storage-mongo


Running examples in docker
--------------------------

For convenience we provide examples of integration with Docker_. To run
examples in docker, you need to have docker and docker-compose installed.

Run application
~~~~~~~~~~~~~~~

Run chat backend with PostgreSQL storage ::

   make run-chat-postgres

Run chat backend with MongoDB storage ::

   make run-chat-mongo

On startup completion you will see output similar to ::

   chat-postgres_1 | ======== Running on http://0.0.0.0:8081 ========
   chat-postgres_1 | (Press CTRL+C to quit)

Open above URL in browser to interact with chat.

Run tests
~~~~~~~~~

Run tests for all examples ::

   make docker-runtests

Run tests for a particular example ::

   make docker-runtests-mockserver-example
   make docker-runtests-mongo-example
   make docker-runtests-chat-storage-postgres


.. _Docker: https://www.docker.com/


Examples
--------

.. toctree::
   :maxdepth: 2

   docker/README
   chat-backend/README
   chat-storage-mongo/README
   chat-storage-postgres/README
