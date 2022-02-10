async def test_messages_send(example_client, mockserver):
    @mockserver.handler('/storage/messages/send')
    async def handle_send(request):
        assert request.json == {
            'username': 'Bob',
            'text': 'Hello, my name is Bob!',
        }
        return mockserver.make_response(status=204)

    response = await example_client.post(
        'messages/send',
        json={'username': 'Bob', 'text': 'Hello, my name is Bob!'},
    )
    assert response.status == 204
    assert handle_send.times_called == 1


async def test_messages_retrieve(example_client, mockserver):
    messages = [
        {
            'username': 'Bob',
            'created': '2020-01-01T12:01:00.000',
            'text': 'Hi, my name is Bob!',
        },
        {
            'username': 'Alice',
            'created': {'$date': '2020-01-01T12:02:00.000'},
            'text': 'Hi Bob!',
        },
    ]

    @mockserver.json_handler('/storage/messages/retrieve')
    async def handle_retrieve(request):
        return {'messages': messages}

    response = await example_client.post('messages/retrieve')
    assert response.status == 200
    body = response.json()
    assert body == {'messages': list(reversed(messages))}
    assert handle_retrieve.times_called == 1
