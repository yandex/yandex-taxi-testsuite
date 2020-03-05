import argparse
import pathlib

import aiohttp
from aiohttp import web

HTTP_TIMEOUT = 10


def main():
    parser = argparse.ArgumentParser(
        description='Testsuite service integration example.',
    )
    parser.add_argument(
        '--storage-service-url',
        help='Url of service responsible for storing messages',
    )
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    storage_service_url = args.storage_service_url
    routes = web.RouteTableDef()
    root = pathlib.Path(__file__).parent
    routes.static('/static', root.joinpath('static'))

    @routes.get('/ping')
    async def handle_ping(request):
        return web.Response(text='OK.')

    @routes.post('/messages/retrieve')
    async def handle_list(request):
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                storage_service_url + 'messages/retrieve',
                timeout=HTTP_TIMEOUT,
            )
            response.raise_for_status()
            response_body = await response.json()
            messages = list(reversed(response_body['messages']))
            result = {'messages': messages}
        return web.json_response(result)

    @routes.post('/messages/send')
    async def handle_send(request):
        body = await request.json()
        message = {'username': body['username'], 'text': body['text']}
        async with aiohttp.ClientSession() as session:
            response = await session.post(
                storage_service_url + 'messages/send',
                json=message,
                timeout=HTTP_TIMEOUT,
            )
            response.raise_for_status()
        return web.Response(status=204)

    @routes.get('/')
    def handle_root(request):
        return web.FileResponse(root.joinpath('chat.html'))

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=args.port)


if __name__ == '__main__':
    main()
