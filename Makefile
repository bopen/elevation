COV_REPORT := html
PYTHON := uv run --frozen

default: qa unit-tests check-typing

check-code:
	$(PYTHON) -m pre_commit run --all-files
	$(PYTHON) -m deptry .

qa: check-code

unit-tests:
	$(PYTHON) -m pytest -vv --cov=. --cov-report=$(COV_REPORT)

integration-tests:
	$(PYTHON) -m pytest -vv --cov=. --cov-report=$(COV_REPORT) tests/integration*.py

all-tests:
	$(PYTHON) -m pytest -vv -n auto --cov=. --cov-report=$(COV_REPORT) tests/test*.py tests/integration*.py

check-typing:
	$(PYTHON) -m mypy .

build-docs:
	$(PYTHON) -m sphinx -W -b html docs docs/_build/html

doc-tests:
	$(PYTHON) -m pytest -vv --doctest-glob="*.md" README.md

test-minimum-versions:
	uv run --isolated --resolution lowest-direct -p python3.11 -m pytest .

minver-tests: test-minimum-versions
