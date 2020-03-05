Testpoint
=========

.. currentmodule:: testsuite.plugins.testpoint

Testpoint is a way to call testcase code from service being teststed.

It has many uses:

- synchronize testcase and service states
- reproduce race condition
- pass data from service to testcase and vice versa
- error injection

Requires service side support for testpoint. Testpoint is implemented as
mockserver handle bound to ``mockserver/testpoint`` path. With simple HTTP
interface:

.. code-block::

  POST /testpoint HTTP/1.0
  Host: mockerver
  Content-Type: appication/json

  {"name": "foo", "data": {"foo": "bar"}}


Service code example:

.. code-block:: cpp

  Response View::Handle(Request&& request) {
    // Testpoint must be enabled for test run
    if (testpoint::IsEnabled()) {
      json::Value data;
      data["foo"] = "bar";
      const auto response = testpoint::Call("foo", data);
      if (respone) {
         // process response if required
      }
    }
  }


Testcase:

.. code-block:: python

   async def test_handler(client, testpoint):
       @testpoint('foo')
       def foo_handler(data):
           pass

       response = await client.post(...)
       assert response.status_code == 200
       assert foo_handler.times_called


Fixtures
--------

.. autofunction:: testpoint(name)
   :no-auto-options:
