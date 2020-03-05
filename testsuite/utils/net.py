import socket

DEFAULT_BACKLOG = 50


def bind_socket(
        hostname='localhost',
        port=0,
        family=socket.AF_INET,
        backlog=DEFAULT_BACKLOG,
):
    sock = socket.socket(family)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((hostname, port))
    sock.listen(backlog)
    return sock
