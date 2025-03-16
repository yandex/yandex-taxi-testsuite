VENV_DOCS_PATH  = .venv-docs
VENV_DEV_PATH   = .venv-dev
VENV_PYTHON     = $(firstword $(shell which python3.9 python3.8 python3.7 python3 2> /dev/null))

VENV_COMMON_DEPS = setup.py setup.cfg requirements.txt
VENV_DEV_DEPS = $(VENV_COMMON_DEPS) docs/examples/requirements.txt
VENV_DOCS_DEPS = $(VENV_COMMON_DEPS) docs/requirements.txt

PY_DIRS = testsuite
PACKAGE_VERSION = $(shell awk '/^version = /{print $$3}' setup.cfg)

TESTSUITE_GH_PAGES_REPO = /tmp/$(USER)/testsuite-gh-pages.git

.PHONY: tests

tests:
	python3 -m pytest -v tests/ $(PYTEST_ARGS)

test-examples:
	make -C docs/examples runtests

check-mypy:
	mypy testsuite tests

check-format:
	ruff format --check --diff .
	ruff check --ignore ALL --select I --diff .

check-linters:
	ruff check $(PY_DIRS) --show-fixes

format:
	ruff format .
	ruff check --ignore ALL --select I --fix .

venv-tests:
venv-check-linters:
venv-check-mypy:
venv-check-format:
venv-format:
venv-start-release:
venv-release-upload-testpypi:
venv-release-upload-pypi:


venv-%: setup-dev-venv
	(. $(VENV_DEV_PATH)/bin/activate && $(MAKE) $*)

setup-dev-venv: $(VENV_DEV_PATH)/.timestamp

$(VENV_DEV_PATH)/.timestamp:  $(VENV_DEV_DEPS)
	test -x $(VENV_DEV_PATH)/bin/python || \
		virtualenv --python=$(VENV_PYTHON) $(VENV_DEV_PATH)
	$(VENV_DEV_PATH)/bin/pip install -r requirements.txt
	$(VENV_DEV_PATH)/bin/pip install -r docs/examples/requirements.txt
	touch $@

setup-docs-venv: $(VENV_DOCS_PATH)/.timestamp

build-docs: build-docs-html

build-docs-%: setup-docs-venv
	(. $(VENV_DOCS_PATH)/bin/activate && PYTHONPATH="$$PYTHONPATH:$(PWD)" \
		$(MAKE) -C docs $*)

$(VENV_DOCS_PATH)/.timestamp: $(VENV_DOCS_DEPS)
	test -x $(VENV_DOCS_PATH)/bin/python || \
		virtualenv --python=$(VENV_PYTHON) $(VENV_DOCS_PATH)
	$(VENV_DOCS_PATH)/bin/pip install -r requirements.txt
	$(VENV_DOCS_PATH)/bin/pip install -r docs/requirements.txt
	touch $@

start-release:
	./tools/release.sh

release-upload-testpypi:
	$(MAKE) release-upload-testpypi-$(PACKAGE_VERSION)

release-upload-pypi:
	$(MAKE) release-upload-pypi-$(PACKAGE_VERSION)

release-upload-pypi-%: dist/%/.timestamp
	python3 -m twine upload --repository pypi dist/$*/*

release-upload-testpypi-%: dist/%/.timestamp
	python3 -m twine upload --repository testpypi dist/$*/*

build-package-%: dist/%/.timestamp
	@echo "Package version $*"

.PRECIOUS: dist/%/.timestamp
dist/%/.timestamp:
	rm -rf $@
	python3 -m build -o dist/$*
	touch $@

publish-gh-pages: build-docs-dirhtml
	./tools/publish-gh-repo.sh $(TESTSUITE_GH_PAGES_REPO) $(PACKAGE_VERSION)

clean:
	rm -rf dist $(VENV_DEV_PATH) $(VENV_DOCS_PATH) docs/_build


install-pre-commit-hooks: .git/hooks/pre-commit

.git/hooks/pre-commit:
	rm -f $@
	ln -s $(PWD)/tools/pre-commit.sh $@
