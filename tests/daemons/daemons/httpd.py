#!/usr/bin/env python3

import argparse
import http.server
import socket
import socketserver
import typing


class ExternalSocketHTTPServer(socketserver.TCPServer):
    def __init__(self, sock, request_handler_class):
        super().__init__(sock.getsockname(), request_handler_class)
        self.socket = sock
        self.server_bind()
        self.server_activate()

    def server_bind(self):
        # Socket is already bound
        host, port = self.server_address[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port


class RequestHandler(http.server.BaseHTTPRequestHandler):
    _GET_methods: typing.Dict[str, typing.Callable] = {}

    def do_GET(self):
        if self.path not in self._GET_methods:
            self.send_error(404, 'Not found')
        else:
            self._GET_methods[self.path](self)

    @classmethod
    def route(cls, path):
        def _route(func):
            cls._GET_methods[path] = func
            return func

        return _route

    def make_response(
        self,
        data,
        *,
        content_type='text/plain',
        status_code=200,
    ):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)


def bind_unused_socket(hostname='localhost'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((hostname, 0))
    return s


@RequestHandler.route('/ping')
def ping(request):
    request.make_response(b'pong')


@RequestHandler.route('/hello')
def hello(request):
    request.make_response(b'Hello, world!\n')


@RequestHandler.route('/exit')
def exit_(request):
    request.make_response(b'Exiting!\n')

    def server_shutdown(server):
        server.shutdown()

    import threading

    thread = threading.Thread(target=server_shutdown, args=(request.server,))
    thread.start()


def server_main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--hostname',
        default='localhost',
        help='Hostname to bind HTTP server (default: %(default)s)',
    )
    parser.add_argument(
        '--port',
        default=8000,
        type=int,
        help='Port to bind HTTP server (default: %(default)s)',
    )
    parser.add_argument(
        '--server-fd',
        type=int,
        help='Server socket descriptor (default: %(default)s)',
    )
    args = parser.parse_args()

    if args.server_fd is not None:
        httpd = ExternalSocketHTTPServer(
            socket.socket(fileno=args.server_fd),
            RequestHandler,
        )
    else:
        httpd = http.server.HTTPServer(
            (args.hostname, args.port),
            RequestHandler,
        )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    server_main()
