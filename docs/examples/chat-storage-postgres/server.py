import argparse

from aiohttp import web
import asyncpg

HTTP_TIMEOUT = 10


def main():
    parser = argparse.ArgumentParser(
        description='Testsuite service integration example.',
    )
    parser.add_argument('--postgresql', help='PostgreSQL connection string')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    web.run_app(create_app(args), port=args.port)


async def create_app(args):
    routes = web.RouteTableDef()

    @routes.get('/ping')
    async def handle_ping(request):
        return web.Response(text='OK.')

    @routes.post('/messages/send')
    async def post(request):
        data = await request.json()
        async with app['pool'].acquire() as connection:
            row_id = await connection.fetchval(
                'INSERT INTO messages(username, text) VALUES ($1, $2) '
                'RETURNING id',
                data['username'],
                data['text'],
            )
        return web.json_response({'id': row_id})

    @routes.post('/messages/retrieve')
    async def get(request):
        async with app['pool'].acquire() as connection:
            records = await connection.fetch(
                'SELECT created, username, "text" FROM messages '
                'ORDER BY created DESC LIMIT 20',
            )
        messages = [
            {
                'created': record[0].isoformat(),
                'username': record[1],
                'text': record[2],
            }
            for record in records
        ]
        return web.json_response({'messages': messages})

    app = web.Application()
    app['pool'] = await asyncpg.create_pool(dsn=args.postgresql)
    app.add_routes(routes)
    return app


if __name__ == '__main__':
    main()
