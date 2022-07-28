#!/bin/bash

find_rabbitmq() {
    if [ ! -x "$RABBITMQ_BINDIR/rabbitmq-server" ]; then
        die "No rabbitmq-server script found. 
Please install RabbitMQ following official instructions at 
https://www.rabbitmq.com/download.html 
or set TESTSUITE_RABBITMQ_BINDIR environment variable to the directory containing
actual rabbitmq scripts (it's usually /usr/lib/rabbitmq/bin/). Note that this directory
differs from \"which rabbitmq-server\", 
actual location can be found via inspecting sbin/rabbitmq-server script.
"
    fi
    if [ ! -x "$RABBITMQ_BINDIR/rabbitmq-server" ]; then
        die "No rabbitmqctl script found. 
Please install RabbitMQ following official instructions at 
https://www.rabbitmq.com/download.html 
or set TESTSUITE_RABBITMQ_BINDIR environment variable to the directory containing
actual rabbitmq scripts (it's usually /usr/lib/rabbitmq/bin/). Note that this directory
differs from \"which rabbitmqctl\", 
actual location can be found via inspecting sbin/rabbitmqctl script.
"
    fi

    return 0
}

find_rabbitmq || die "RabbitMQ is not found."
