FROM ubuntu:18.04

RUN apt-get update && \
    apt-get install -y python3.7 python3-virtualenv postgresql-client && \
    apt-get clean

RUN mkdir -p /opt/yandex
RUN python3.7 -m virtualenv --python=/usr/bin/python3.7 /opt/yandex/testsuite

RUN mkdir -p /tmp/testsuite

# Early install requirements
COPY setup.py setup.cfg /tmp/testsuite/
COPY testsuite /tmp/testsuite/testsuite/

RUN /opt/yandex/testsuite/bin/pip install /tmp/testsuite[mongodb,postgresql-binary]

# Example requirements
RUN /opt/yandex/testsuite/bin/pip install asyncpg motor
