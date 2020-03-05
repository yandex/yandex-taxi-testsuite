async def test_messages_send(server_client, pgsql):
    response = await server_client.post(
        '/messages/send', json={'username': 'foo', 'text': 'bar'},
    )
    assert response.status_code == 200
    data = response.json()
    assert 'id' in data

    cursor = pgsql['chat_messages'].cursor()
    cursor.execute(
        'SELECT username, text FROM messages WHERE id = %s', (data['id'],),
    )
    record = cursor.fetchone()
    assert record == ('foo', 'bar')


async def test_messages_retrieve(server_client, pgsql):
    response = await server_client.post('/messages/retrieve', json={})
    assert response.json() == {
        'messages': [
            {
                'created': '2019-12-31T21:00:01+00:00',
                'text': 'happy ny',
                'username': 'bar',
            },
            {
                'created': '2019-12-31T21:00:00+00:00',
                'text': 'hello, world!',
                'username': 'foo',
            },
        ],
    }
