.PHONY: help test build twine-check smoke clean

PY ?= python3

help:
	@echo "Targets:"
	@echo "  make test        - run unit tests"
	@echo "  make build       - build sdist + wheel"
	@echo "  make twine-check - sanity check dist metadata"
	@echo "  make smoke       - install wheel in fresh venv + run import/CLI"
	@echo "  make clean       - remove build artifacts"

test:
	$(PY) -m pip install -U pytest
	$(PY) -m pytest -q

build:
	$(PY) -m pip install -U build
	$(PY) -m build

twine-check:
	$(PY) -m pip install -U "twine>=6.1.0" "packaging>=24.2"
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
