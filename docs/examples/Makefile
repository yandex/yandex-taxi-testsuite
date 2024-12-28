PYTHON     = $(firstword $(shell which python3.9 python3.8 python3.7 python3))
PYTEST      ?= $(PYTHON) -m pytest
PYTEST_ARGS ?= -vv

EXAMPLES =					\
	chat-backend				\
	chat-storage-mongo			\
	chat-storage-postgres			\
	chat-storage-mysql

RUNTEST_TARGETS = $(foreach example,$(EXAMPLES),runtests-$(example))
DOCKER_TARGETS = $(foreach example,$(EXAMPLES),docker-runtests-$(example))
RUN_TARGETS = $(foreach example,$(EXAMPLES),run-$(example))

runtests: $(RUNTEST_TARGETS)
docker-runtests: | $(DOCKER_TARGETS)

$(RUNTEST_TARGETS): runtests-%:
	PYTHONPATH=../.. $(PYTEST) $(PYTEST_ARGS) $*/tests

$(DOCKER_TARGETS): docker-runtests-%: docker-image
	docker-compose -f docker/docker-compose.yaml run runtests-$* \
		pytest $(PYTEST_ARGS) $*/tests

$(RUN_TARGETS): run-%: docker-image
	docker-compose -f docker/docker-compose.yaml run $*

docker-image: .docker-image-timestamp

.docker-image-timestamp: docker/testsuite/Dockerfile
	docker build -t testsuite -f docker/testsuite/Dockerfile ../..
	touch $@

clean:
	rm -f .docker-image-timestamp
