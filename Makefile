.PHONY: help venv install test build clean

help:
	@echo "make venv     - create .venv"
	@echo "make install  - editable install + dev tools"
	@echo "make test     - run tests"
	@echo "make build    - build wheel/sdist"
	@echo "make clean    - remove build artifacts"

venv:
	python -m venv .venv

install:
	. .venv/bin/activate && python -m pip install -U pip
	. .venv/bin/activate && python -m pip install -e .
	. .venv/bin/activate && python -m pip install -U pytest build twine

test:
	. .venv/bin/activate && pytest -q

build:
	. .venv/bin/activate && python -m build

clean:
	rm -rf dist build src/*.egg-info src/**/__pycache__ tests/**/__pycache__ .pytest_cache

