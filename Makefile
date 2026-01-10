.PHONY: help dev lint lint-fix test build twine-check smoke all clean

SHELL := /bin/bash
PY ?= python3
WHEELTEST_DIR ?= /tmp/la-wheeltest

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
	$(PY) -m pip install -e ".[dev]"

lint:
	$(PY) -m ruff check .

lint-fix:
	$(PY) -m ruff check . --fix

test:
	$(PY) -m pytest -q

build:
	$(PY) -m build

twine-check:
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
