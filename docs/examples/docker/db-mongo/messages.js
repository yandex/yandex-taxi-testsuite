db_chat = db.getSiblingDB('db_chat');
db_chat.messages.createIndex({'created': 1});
