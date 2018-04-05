install:
	pip install -r requirements.txt

install-test:
	pip install -r requirements-tests.txt

test:
	py.test --cov leapp

.PHONY: install install-test test
