Mockserver
==========

.. currentmodule:: testsuite.plugins.mockserver

Mockserver is a simple http server running inside pytest instance.
Using ``mockserver`` fixture you can install per-test handler.

Tested service should be configured to pass all HTTP calls to mockserver, e.g.:

.. code-block::

   http://mockserver-address/service-name/path

If there is no mockserver handler installed for path mockserver returns
HTTP 500 error and fails current test. This behaviour could be switched off
with ``--mockserver-nofail`` command-line option.


Example:

.. code-block:: python

  async def test_mockserver(service_client, mockserver):
      @mockserver.json_handler('/service-name/path')
      def handler(request: testsuite.utils.http.Request):
          assert request.headers['header-to-test'] == '...'
          assert request.json == {...}
          reutrn {...}

      response = await service_client.post(...)
      assert response.status_code == 200
      assert response.json() == {...}

      # Ensure handler was used
      assert handler.times_called == 1

Fixtures
--------

mockserver
~~~~~~~~~~

.. autofunction:: mockserver()
   :no-auto-options:

   Returns an instance of :py:class:`HandlerInstaller`.

.. autoclass:: HandlerInstaller()
    :members:

mockserver_info
~~~~~~~~~~~~~~~

.. autofunction:: mockserver_info()
   :no-auto-options:

   Returns ``MockserverInfo`` instance containing basic information about
   mockserver.

.. autoclass:: MockserverInfo()
    :members:


Timeouts and network errors
---------------------------

Mockserver supports timeouts and network errors emulation this requires
service's HTTP client support. It should specify supported error codes
while performing request to mockserver:

.. code-block:: text

   GET /path HTTP/1.1
   X-Testsuite-Supported-Errors: network,timeout
   ...

This feature should be turned off in production run.

Mockserver will respone with 599 HTTP error and testsuite-specific error code,
HTTP client should raise its own internal exception corresponding to the error
code:

.. code-block:: text

   HTTP/1.1 599 testsuite-error
   X-Testsuite-Error: network|timeout
   ...

And on the service side:


.. code-block:: cpp

   Response HttpClient::request(const Request& request) {
     auto response = PerformRequest(request);
     if (response.status_code == 599 &&
        request.hasHeader("X-Testsuite-Error")) {
       const auto &testsuite_error =
           respones.getHeader("X-Testsuite-Error");
       if (testsuite_error == "network")
         throw NetworkError();
       if (testsuite_error == "timeout")
         throw TimeoutError()
       throw std::runtime_error("Unhandled error code");
      }
      return response;
   }

Then you can raise mockserver error in the testcase, e.g.:

.. code-block:: python

    async def test_timeout(service_client, mockserver):
        @mockserver.handler('/service/handle')
        def handle(request):
            raise mockserver.TimeoutError()
        response = await service_client.get('...')
        assert ...

Available errors are:

* :py:class:`HandlerInstaller.TimeoutError`
* :py:class:`HandlerInstaller.NetworkError`

OpenTracing
-----------

To make tests fast, testsuite starts the service only once, at the beginning of
test session.

Consider a test case, when service starts a background task which periodically
calls external service. Suppose the task continues after test completion.

Now recall that by default testsuite requires *all* calls to external services,
which happen in test case, to be mocked.

Observe, the background task started in one test, causes http requests to
mockserver, while another test is running, which will cause it to fail unless
it is happens to be mocked in another test.

What choices are there to make another test pass:

* Setup global mocks for any external APIs called from background tasks. It is
  undesirable because these mocks are only actually required by some of the
  tests.
* Run testsuite with ``--mockserver-nofail`` flag. It is also undesirable
  because the developer is not warned anymore if he actually forgets to mock an
  external call.

As long as your services support `OpenTracing <https://opentracing.io/>`_-like
distributed request tracing, there is a good solution to the problem.

When processing an unmocked http call to external service, mockserver takes
advantage of OpenTracing http headers to tell whether or not the request was
caused by current test case.

If the unhandled request was caused from current test case, mockserver
terminates the test with error, as usually.

If the call is unrelated to current test case, mockserver acts as if
``--mockserver-nofail`` flag was specified, it responds with HTTP status 500
and test case proceeds normally.

OpenTracing can be enabled in ``pytest.ini`` ::

 mockserver-tracing-enabled = true
 mockserver-trace-id-header = X-TraceId
 mockserver-span-id-header = X-SpanId
