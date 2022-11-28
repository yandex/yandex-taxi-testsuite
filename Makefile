VENV_DOCS_PATH  = $(CURDIR)/.venv-docs
VENV_DEV_PATH   = $(CURDIR)/.venv-dev
VENV_PYTHON     = $(firstword $(shell which python3.9 python3.8 python3.7 python3))

PY_DIRS = testsuite
PACKAGE_VERSION = $(shell awk '/^version = /{print $$3}' setup.cfg)

.PHONY: tests

tests:
	python3 -m pytest -v tests/ $(PYTEST_ARGS)

test-examples:
	make -C docs/examples runtests

linters:
# stop the build if there are Python syntax errors or undefined names
	flake8 $(PY_DIRS) --count --select=E9,F63,F7,F82 --show-source --statistics
# exit-zero treats all errors as warnings. The GitHub editor is 127 chars wide
	flake8 $(PY_DIRS) --count --exit-zero --max-complexity=10 --max-line-length=79 --statistics

venv-linters:
venv-tests:

venv-%: setup-dev-venv
	PATH=$(VENV_DEV_PATH)/bin:$(PATH) $(MAKE) $*

setup-dev-venv: $(VENV_DEV_PATH)/.timestamp

$(VENV_DEV_PATH)/.timestamp: setup.py setup.cfg requirements.txt docs/examples/requirements.txt
	test -x $(VENV_DEV_PATH)/bin/python || \
		virtualenv --python=$(VENV_PYTHON) $(VENV_DEV_PATH)
	$(VENV_DEV_PATH)/bin/pip install -r requirements.txt
	$(VENV_DEV_PATH)/bin/pip install -r docs/examples/requirements.txt
	touch $@

setup-docs-venv: $(VENV_DOCS_PATH)/.timestamp

build-docs: build-docs-html

build-docs-%: setup-docs-venv
	PATH=$(VENV_DOCS_PATH)/bin:$(PATH) PYTHONPATH=$(PWD) \
		$(MAKE) -C docs $*

$(VENV_DOCS_PATH)/.timestamp: setup.py setup.cfg docs/requirements.txt
	test -x $(VENV_DOCS_PATH)/bin/python || \
		virtualenv --python=$(VENV_PYTHON) $(VENV_DOCS_PATH)
	$(VENV_DOCS_PATH)/bin/pip install -r docs/requirements.txt
	touch $@

start-release:
	./tools/release.sh

release-upload-testpypi:
	$(MAKE) release-upload-testpypi-$(PACKAGE_VERSION)

release-upload-pypi:
	$(MAKE) release-upload-testpypi-$(PACKAGE_VERSION)

release-upload-pypi-%: dist/%/.timestamp
	python3 -m twine upload --repository pypi dist/$*/*

release-upload-testpypi-%: dist/%/.timestamp
	python3 -m twine upload --repository testpypi dist/$*/*

build-package-%: dist/%/.timestamp
	@echo "Package version $*"

dist/%/.timestamp:
	rm -rf $@
	python3 -m build -o dist/$*
	touch $@
