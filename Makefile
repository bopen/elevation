COV_REPORT := html
PYTHON := uv run --frozen

default: qa unit-tests check-typing

qa:
	$(PYTHON) -m pre_commit run --all-files

unit-tests:
	$(PYTHON) -m pytest -vv --cov=. --cov-report=$(COV_REPORT)

check-typing:
	$(PYTHON) -m mypy .

docs-build:
	$(PYTHON) -m sphinx -W -b html docs docs/_build/html

doc-tests:
	$(PYTHON) -m pytest -vv --doctest-glob="*.rst" README.rst

minver-tests:
	uv run --resolution lowest-direct -p python3.11 --extra reference -m pytest .
