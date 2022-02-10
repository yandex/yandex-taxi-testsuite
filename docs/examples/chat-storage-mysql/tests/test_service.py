async def test_messages_send(example_client, mysql):
    response = await example_client.post(
        '/messages/send', json={'username': 'foo', 'text': 'bar'},
    )
    assert response.status_code == 200
    data = response.json()
    assert 'id' in data

    cursor = mysql['chat_messages'].cursor()
    cursor.execute(
        'SELECT username, text FROM messages WHERE id = %s', (data['id'],),
    )
    record = cursor.fetchone()
    assert record == ('foo', 'bar')


async def test_messages_retrieve(example_client):
    response = await example_client.post('/messages/retrieve', json={})
    assert response.json() == {
        'messages': [
            {
                'created': '2019-12-31T21:00:01',
                'text': 'happy ny',
                'username': 'bar',
            },
            {
                'created': '2019-12-31T21:00:00',
                'text': 'hello, world!',
                'username': 'foo',
            },
        ],
    }
