Http mockserver
===============

.. currentmodule:: testsuite.mockserver

Mockserver is a simple http server running inside pytest instance.
Using ``mockserver`` fixture you can install per-test handler.

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


Tested service should be configured to pass all HTTP calls to mockserver, e.g.:

.. code-block::

   http://mockserver-address/service-name/path

In order to achieve this you should point your service to mockserver instead
of original service url.

You can use session fixture :py:meth:`mockserver_info.url()<.classes.MockserverInfo.url>` to build mockserver url, e.g.:

.. code-block::

   @pytest.fixture(scope='session')
   def service_args(mockserver_info):
       """Build service startup args."""
       return (
           'bin/service',
           '--service1-base-url',
           mockserver_info.url('service1'),
           '--service2-base-url',
           mockserver_info.url('service2'),
       )


Usually your service takes config file as an argument.
In this case you should provide fixture that creates config file
and substitutes all testsuite related parameters.

Creating custom mockserver
--------------------------

Sometimes it's required to create a specific mockserver. This could be achieved this way:

.. code-block::

   @pytest.fixture
   async def my_mockserver(
       _my_mockserver: server.Server,
       mockserver_create_session,
   ):
       async with mockserver_create_session(_my_mockserver) as session:
           yield session


   @pytest.fixture(scope='session')
   async def _my_mockserver(mockserver_create):
       async with _mockserver_create() as server:
           yield server


Command line options
--------------------

.. _--mockserver-nofail:

--mockserver-nofail
~~~~~~~~~~~~~~~~~~~

If there is no mockserver handler installed for path mockserver returns
HTTP 500 error and fails current test. This behaviour could be switched off
with ``--mockserver-nofail`` command-line option.

--mockserver-host HOST
~~~~~~~~~~~~~~~~~~~~~~

Explicitly set HTTP mockserver hostname to bind to. Default is **localhost**.

--mockserver-port PORT
~~~~~~~~~~~~~~~~~~~~~~

Explicitly set HTTP mockserver. Default is **0** which means bind to random port.

--mockserver-ssl-host HOST
~~~~~~~~~~~~~~~~~~~~~~~~~~

Explicitly set HTTPs mockserver hostname to bind to. Default is **localhost**.

--mockserver-ssl-port PORT
~~~~~~~~~~~~~~~~~~~~~~~~~~

Explicitly set HTTPs mockserver. Default is **0** which means bind to random port.

--mockserver-unix-socket PATH
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bind mockserver to unix domain socket. ``--mockserver-host`` and ``--mockserver-port`` options will be ignored.

pytest.ini options
------------------

mockserver-tracing-enabled
~~~~~~~~~~~~~~~~~~~~~~~~~~

Boolean flags. Controls how mockserver takes requests with trace-id header set.

When request trace-id header not from testsuite:
 - **True**: handle, if handler missing return http status 500
 - **False**: handle, if handler missing raise **HandlerNotFoundError**

When request trace-id header from other test:
 - **True**: do not handle, return http status 500
 - **False**: handle, if handler missing raise **HandlerNotFoundError**

mockserver-trace-id-header
~~~~~~~~~~~~~~~~~~~~~~~~~~

Name of tracing http header, value changes from test to test and is constant within test.
Default value is **X-YaTraceId**.

mockserver-span-id-header
~~~~~~~~~~~~~~~~~~~~~~~~~

Name of tracing http header, value is unique for each request. Default value is **X-YaSpanId**.

mockserver-ssl-cert-file
~~~~~~~~~~~~~~~~~~~~~~~~

Path to ssl certificate file to setup mockserver_ssl.

mockserver-ssl-key-file
~~~~~~~~~~~~~~~~~~~~~~~

Path to ssl key file to setup mockserver_ssl.

mockserver-http-proxy-enabled
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When enabled mockserver acts as http proxy. Is disabled by default.

Fixtures
--------

.. currentmodule:: testsuite.mockserver.pytest_plugin

mockserver
~~~~~~~~~~

Test scoped fixture. Mockserver is already running when it's requested.

.. autofunction:: mockserver()
   :no-auto-options:

   Returns an instance of
   :py:class:`testsuite.mockserver.server.MockserverFixture`.

.. autoclass:: testsuite.mockserver.server.MockserverFixture()
    :members:

mockserver_info
~~~~~~~~~~~~~~~

Session scoped fixture. Contains all information about mockserver: host, port, etc.

.. autofunction:: mockserver_info()
   :no-auto-options:

   Returns :py:class:`testsuite.mockserver.classes.MockserverInfo` instance
   containing basic information about
   mockserver.

.. autoclass:: testsuite.mockserver.classes.MockserverInfo()
    :members:


Magic args
----------

By default mockserver handler receives :py:class:`testsuite.utils.http.Request`
or :py:class:`aiohttp.web.BaseRequest` object. Mockserver also supports special
arguments that are filled with values from request, e.g.:

.. code-block:: python

  async def test_mockserver(service_client, mockserver):
      @mockserver.json_handler('/service-name/path')
      def handler(*, body_json, method):
          assert method == 'POST'
          assert body_json == {...}
          reutrn {...}


Currently supported arguments are:

=============   ==============================
Name            Meaning
=============   ==============================
body_binary     Request body as binary
body_json       Request body as JSON object
content_type    Content-Type header value
cookies         Cookies dictionary
form            Form data
headers         Headers dictionary
method          HTTP method string
path            Request path
query           Query dictionary
=============   ==============================

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

* :py:class:`testsuite.mockserver.server.MockserverFixture.TimeoutError`
* :py:class:`testsuite.mockserver.server.MockserverFixture.NetworkError`

Mockserver Routing
------------------

Mockserver matches HTTP calls to handlers based on the request path. 
By default, they are compared for equality. 

`regex=True` allows you to compare paths using regular expressions. 
The values of named groups are passed to the handler method parameters 
of the same name.

.. code-block:: python

   @mockserver.json_handler(r'/lib/(?P<lib_id>\w+)/books/(?P<book_id>\w+)', regex=True)
   def handler(request, lib_id, book_id):
        # When requesting POST /lib/mylib/books/mybook
        # `mylib` will be passed to lib_id and
        # `mybook` will be passed to book_id.
        return {}

The path is checked for compliance with the entire pattern 
:py:meth:`pattern.fullmatch`, so you do not need to add `^$` markers for the 
beginning/ending of the line.

`prefix=True` allows you to match the handler path to the beginning of the 
path in the http request.

.. code-block:: python

   @mockserver.json_handler('/foo', prefix=True)
   def handler(request):
       # Will handle both `/foo` and `/foo/bar`
       # POST requests.
       return {}

WebSocket support
-----------------

Mockserver supports WebSocket connections.

Example:

.. code-block:: python

   @mockserver.aiohttp_handler('/ws/chat')
   async def ws_handler(request):
       ws = aiohttp.web.WebSocketResponse()
       await ws.prepare(request)

       async for msg in ws:
           if msg.type == aiohttp.WSMsgType.TEXT:
               await ws.send_str(msg.data)
           elif msg.type == aiohttp.WSMsgType.BINARY:
               await ws.send_bytes(msg.data)
           elif msg.type == aiohttp.WSMsgType.ERROR:
               break

       return ws

OpenTracing
-----------

To make tests fast, testsuite starts the service only once, at the beginning of
test session.

Consider a test case *TestA*, when service starts a background task which
periodically calls external service. Suppose the task continues after test
completion.

Observe, the background task started in *TestA*, causes http requests to
mockserver, while another *TestB* is running.

Now recall that by default testsuite requires *all* calls to external services,
which happen in test case, to be mocked.

It causes *TestB* to fail while handling request from *TestA* unless request
from *TestA* coincidentally happens to be mocked in *TestB*.

What choices are there to make *TestB* pass:

* Setup global mocks for any external APIs called from background tasks. It is
  undesirable because these mocks are only actually required by some of the
  tests.
* Run testsuite with :ref:`--mockserver-nofail` flag. It is also undesirable
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
:ref:`--mockserver-nofail` flag was specified, it responds with HTTP status 500
and test case proceeds normally.

OpenTracing can be enabled in ``pytest.ini`` ::

 mockserver-tracing-enabled = true
 mockserver-trace-id-header = X-TraceId
 mockserver-span-id-header = X-SpanId

