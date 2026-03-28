.PHONY: install-dev run diagnostics test lint build clean

VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
APP ?= $(VENV)/bin/asus-linux-control-center

install-dev:
	python3 -m venv --system-site-packages $(VENV)
	$(PYTHON) -m pip install -U pip
	$(PIP) install -e .[dev]

run:
	PYTHONPATH=src python3 -m asus_linux_control_center

diagnostics:
	PYTHONPATH=src python3 -m asus_linux_control_center --diagnostics

test:
	PYTHONPATH=src $(PYTHON) -m pytest

lint:
	PYTHONPATH=src $(PYTHON) -m ruff check src tests

build:
	PYTHONPATH=src $(PYTHON) -m build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
	rm -rf .pytest_cache .ruff_cache build dist src/*.egg-info
