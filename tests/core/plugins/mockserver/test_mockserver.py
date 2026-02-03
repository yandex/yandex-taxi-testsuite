# pylint: disable=protected-access
import socket

import aiohttp
import aiohttp.web
import pytest

import testsuite
from testsuite.mockserver import exceptions

from .client import Client


class UserError(Exception):
    pass


@pytest.fixture
async def mockserver_client(mockserver: testsuite.MockserverFixture):
    async with aiohttp.ClientSession() as session:
        yield Client(base_url=mockserver.base_url, session=session)


async def test_json_handler(
    mockserver: testsuite.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    def _foo_handler(request):
        return {'msg': 'hello'}

    response = await mockserver_client.get('/foo')
    assert response.status == 200
    data = await response.json()

    assert data == {'msg': 'hello'}


async def test_async_json_handler(
    mockserver: testsuite.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    async def _foo_handler(request):
        return {'msg': 'hello'}

    response = await mockserver_client.get('/foo')
    assert response.status == 200
    data = await response.json()

    assert data == {'msg': 'hello'}


async def test_handler(
    mockserver: testsuite.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    def _foo_handler(request):
        return mockserver.make_response('hello')

    response = await mockserver_client.get('/foo')
    assert response.status == 200
    data = await response.content.read()

    assert data == b'hello'


async def test_user_error(
    mockserver: testsuite.MockserverFixture,
    mockserver_client: Client,
    mockserver_errors_list,
    mockserver_errors_pop,
):
    @mockserver.json_handler('/foo')
    def _foo_handler(request):
        raise UserError

    response = await mockserver_client.get('/foo')
    assert response.status == 500

    assert len(mockserver_errors_list) == 1

    error = mockserver_errors_pop()
    assert isinstance(error, UserError)


async def test_nohandler(
    mockserver: testsuite.MockserverFixture,
    mockserver_client: Client,
    mockserver_errors_list,
    mockserver_errors_pop,
):
    response = await mockserver_client.get(
        '/foo123',
        headers={mockserver.trace_id_header: mockserver.trace_id},
    )
    assert response.status == 500

    assert len(mockserver_errors_list) == 1

    error = mockserver_errors_pop()
    assert isinstance(error, exceptions.HandlerNotFoundError)


async def test_aiohttp_response(
    mockserver: testsuite.MockserverFixture,
    mockserver_client: Client,
):
    @mockserver.json_handler('/foo')
    def _foo_handler(request):
        return aiohttp.web.json_response({'foo': 'bar'})

    response = await mockserver_client.get('/foo')

    assert response.status == 200
    assert await response.json() == {'foo': 'bar'}


async def test_direct_addresses(
    mockserver, mockserver_client, _mockserver_socket
):
    @mockserver.json_handler('/foo')
    def handler(request):
        return {}

    def build_addr(sock):
        addr, port, *_ = sock.getsockname()
        if sock.family == socket.AF_INET6:
            return f'[{addr}]', port
        elif sock.family == socket.AF_INET:
            return f'{addr}', port
        raise RuntimeError(f'Unknown socket family {sock}')

    async with aiohttp.ClientSession() as session:
        for sock in _mockserver_socket.sockets:
            addr, port = build_addr(sock)
            response = await session.get(
                f'http://{addr}:{port}/foo',
                timeout=10.0,
                headers={'Host': f'localhost:{port}'},
            )
            assert response.status == 200
