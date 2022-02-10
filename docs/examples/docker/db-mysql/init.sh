#!/bin/sh

set -ex

mysql -u root <<EOF
CREATE DATABASE chat_messages;
EOF

for schema in /schemas/*.sql; do
    mysql -u root --database=chat_messages "source $schema";
done
