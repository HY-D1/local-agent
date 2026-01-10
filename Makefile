.PHONY: help dev tools lint lint-fix test build twine-check smoke all clean

SHELL := /bin/bash
PY ?= python3
WHEELTEST_DIR ?= /tmp/la-wheeltest
DEV_TOOLS := ruff pytest build twine "pkginfo>=1.12.0"

help:
	@echo "Targets:"
	@echo "  make dev         - install dev tools (ruff/pytest/build/twine/pkginfo)"
	@echo "  make lint        - run ruff"
	@echo "  make lint-fix    - ruff --fix"
	@echo "  make test        - run unit tests"
	@echo "  make build       - build sdist + wheel"
	@echo "  make twine-check - sanity check dist metadata"
	@echo "  make smoke       - install wheel in fresh venv + run import/CLI"
	@echo "  make all         - clean + lint + test + build + twine-check + smoke"
	@echo "  make clean       - remove build artifacts"

dev:
	$(PY) -m pip install -U pip
	$(MAKE) tools

tools:
	$(PY) -m pip install -U $(DEV_TOOLS)

lint: tools
	$(PY) -m ruff check .

lint-fix: tools
	$(PY) -m ruff check . --fix

test: tools
	$(PY) -m pytest -q

build: tools
	$(PY) -m build

twine-check: tools
	$(PY) -m twine check dist/*

smoke: build
	rm -rf $(WHEELTEST_DIR)
	$(PY) -m venv $(WHEELTEST_DIR)
	. $(WHEELTEST_DIR)/bin/activate && \
		python -m pip install -U pip && \
		python -m pip install dist/*.whl && \
		python -c "import local_agent; print(local_agent.__version__)" && \
		local-agent --help >/dev/null && \
		local-agent commands

all: clean lint test build twine-check smoke

clean:
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} \;
