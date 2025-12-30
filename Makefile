.PHONY: help test lint format build twine-check smoke clean

PY ?= python3

help:
	@echo "Targets:"
	@echo "  make test        - run unit tests"
	@echo "  make lint        - run ruff lint checks"
	@echo "  make format      - run ruff formatter"
	@echo "  make build       - build sdist + wheel"
	@echo "  make twine-check - sanity check dist metadata"
	@echo "  make smoke       - install wheel in fresh venv + run import/CLI"
	@echo "  make clean       - remove build artifacts"

test:
	$(PY) -m pip install -U pytest
	$(PY) -m pytest -q

lint:
	$(PY) -m pip install -U ruff
	$(PY) -m ruff check .

lint-fix:
	$(PY) -m pip install -U ruff
	$(PY) -m ruff check . --fix

format:
	$(PY) -m pip install -U ruff
	$(PY) -m ruff format .

build:
	$(PY) -m pip install -U build
	$(PY) -m build

twine-check:
	$(PY) -m pip install -U twine "pkginfo>=1.12.0"
	$(PY) -m twine check dist/*

smoke: build
	rm -rf /tmp/la-wheeltest
	$(PY) -m venv /tmp/la-wheeltest
	. /tmp/la-wheeltest/bin/activate && \
	python -m pip install -U pip && \
	python -m pip install dist/*.whl && \
	python -c "import local_agent; print(local_agent.__version__)" && \
	local-agent --help && \
	local-agent commands

clean:
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} \;

install-dev:
	$(PY) -m pip install -U pip
	$(PY) -m pip install -e ".[dev]"
