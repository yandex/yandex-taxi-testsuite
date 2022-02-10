async def test_messages_send(example_client, mongodb):
    message = {
        'username': 'Alice',
        'text': 'Rabbits are so cute, love them ^_^',
    }
    response = await example_client.post('messages/send', json=message)
    assert response.status_code == 200
    body = response.json()
    msg_id = body['id']

    # read directly from mongodb
    stored_message = mongodb['messages'].find_one({'_id': msg_id})
    stored_message.pop('_id')
    stored_message.pop('created')
    assert stored_message == message


async def test_messages_retrieve(example_client):
    # db_messages.json
    read_response = await example_client.post('messages/retrieve')
    assert read_response.status_code == 200
    doc = read_response.json()
    assert doc == {
        'messages': [
            {
                'username': 'Alice',
                'created': '2020-01-01T12:02:00',
                'text': 'Hi Bob!',
            },
            {
                'username': 'Bob',
                'created': '2020-01-01T12:01:00',
                'text': 'Hi, my name is Bob!',
            },
        ],
    }
