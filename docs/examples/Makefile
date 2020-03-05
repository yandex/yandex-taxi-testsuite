PYTEST      ?= python3.7 -m pytest
PYTEST_ARGS ?= -vv

EXAMPLES =					\
	chat-backend				\
	chat-storage-mongo			\
	chat-storage-postgres

RUNTEST_TARGETS = $(foreach example,$(EXAMPLES),runtests-$(example))
DOCKER_TARGETS = $(foreach example,$(EXAMPLES),docker-runtests-$(example))

runtests: $(RUNTEST_TARGETS)
docker-runtests: | $(DOCKER_TARGETS)

$(RUNTEST_TARGETS): runtests-%:
	PYTHONPATH=../.. $(PYTEST) $(PYTEST_ARGS) $*/tests

$(DOCKER_TARGETS): docker-runtests-%: docker-image
	docker-compose -f docker/docker-compose.yaml run runtests-$* \
		pytest $(PYTEST_ARGS) $*/tests

docker-image: .docker-image-timestamp

.docker-image-timestamp: docker/testsuite/Dockerfile
	docker build -t testsuite -f docker/testsuite/Dockerfile ../..
	touch $@

run-chat-mongo: docker-image
	docker-compose -f docker/docker-compose.yaml up chat-mongo

run-chat-postgres: docker-image
	docker-compose -f docker/docker-compose.yaml up chat-postgres

clean:
	rm -f .docker-image-timstamp
