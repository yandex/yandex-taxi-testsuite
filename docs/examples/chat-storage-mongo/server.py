import argparse
import uuid

from aiohttp import web
from motor import motor_asyncio
import pymongo

HTTP_TIMEOUT = 10


def main():
    parser = argparse.ArgumentParser(
        description='MongoDB based storage service.',
    )
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument(
        '--mongo-uri',
        default='mongodb://localhost:27017/',
        help='mongodb connection uri',
    )

    args = parser.parse_args()
    connection = motor_asyncio.AsyncIOMotorClient(args.mongo_uri)
    collection = connection['chat_db']['messages']
    routes = web.RouteTableDef()

    @routes.get('/ping')
    async def handle_ping(request):
        return web.Response(text='OK.')

    @routes.post('/messages/send')
    async def post(request):
        doc = await request.json()
        doc_id = uuid.uuid4().hex
        await collection.update_one(
            {'_id': doc_id},
            {
                '$set': {'username': doc['username'], 'text': doc['text']},
                '$currentDate': {'created': True},
            },
            upsert=True,
        )
        return web.json_response({'id': doc_id})

    @routes.post('/messages/retrieve')
    async def get(request):
        docs = await (
            collection.find({}).sort('created', pymongo.DESCENDING).limit(20)
        ).to_list(20)
        messages = [
            {
                'username': doc['username'],
                'text': doc['text'],
                'created': doc['created'].isoformat(),
            }
            for doc in docs
        ]
        return web.json_response({'messages': messages})

    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=args.port)


if __name__ == '__main__':
    main()
