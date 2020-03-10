What is testsuite
-----------------

Testsuite is a microservice-oriented test framework written in Python based on
pytest_.

Testsuite is written and supported by Yandex.Taxi_, and is used to test
Yandex.Taxi microservices written in C++ and Python.

The principal suggested approach to testing - although not the only one - is
black box, when the service is tested through http calls.

Direct read and write access from test to database is supported to enable
precondition setup and result assertions.

Supported databases
-------------------

Out-of-the-box testsuite supports the following databases:

* PostgreSQL
* MongoDB
* Redis

Supported operating systems
---------------------------

Testsuite runs on GNU/Linux and macOS operating systems.

Principle of operation
----------------------

Testsuite sets up the environment for the service being tested:

* Testsuite starts any required databases (postgresql, mongo, redis).
* Before each test, testsuite fills the database with test data.
* Testsuite starts its own web server (mockserver), which mimics (mocks)
  microservices other than the one being tested.

Testsuite starts the microservice being tested in a separate process.

Testsuite then runs tests.

A test performs http requests to the service and verifies that the requests
were processed properly.

A test may check the results of an http call by looking directly into the
service's database.

A test may check whether the service has made calls to external services,
as well as the order of calls and the data that was sent and received.

A test may check the internal state of the service as represented by the data
the service sent to the test with the testpoint mechanism.

Source code
-----------

Testsuite open-source edition code is available
`here <https://github.com/yandex/yandex-taxi-testsuite>`_.

Documentation
-------------

For full documentation, including installation, tutorials,
please see https://yandex.github.io/yandex-taxi-testsuite/.


Running testsuite
-----------------

self-tests::

   pytest3 ./tests

tests of example services::

   cd docs/examples && make

.. _Yandex.Taxi: https://taxi.yandex.com/company/
.. _pytest: https://pytest.org/
