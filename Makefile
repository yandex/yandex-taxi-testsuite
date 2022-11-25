VENV_DOCS_PATH  = $(CURDIR)/.venv-docs
VENV_PYTHON     = $(firstword $(shell which python3.9 python3.8 python3.7 python3))

setup-docs-venv: $(VENV_DOCS_PATH)/.timestamp

build-docs: build-docs-html

build-docs-%: setup-docs-venv
	PATH=$(VENV_DOCS_PATH)/bin:$(PATH) PYTHONPATH=$(PWD) \
		$(MAKE) -C docs $*

$(VENV_DOCS_PATH)/.timestamp: setup.py setup.cfg docs/requirements.txt
	test -x $(VENV_DOCS_PATH)/bin/python || \
		virtualenv --python=$(VENV_PYTHON) $(VENV_DOCS_PATH)
	$(VENV_DOCS_PATH)/bin/pip install -i https://pypi.yandex-team.ru/simple/ \
		-r docs/requirements.txt
	touch $@
