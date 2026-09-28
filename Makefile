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
	cp README.rst docs/. && cd docs && rm -fr _api && make clean && make html

doc-tests:
	$(PYTHON) -m pytest -vv --doctest-glob="*.rst" README.rst
