CONFDIR=${DESTDIR}/etc/leapp
LIBDIR=${DESTDIR}/var/lib/leapp

install-deps:
	pip install -r requirements.txt

install:
	install -dm 0755 ${CONFDIR}
	install -m 0744 etc/leapp/leapp.conf ${CONFDIR}
	install -m 0744 etc/leapp/logger.conf ${CONFDIR}
	install -dm 0755 ${LIBDIR}
	umask 0600
	python -c "import sqlite3; sqlite3.connect('${LIBDIR}/audit.db').executescript(open('res/audit-layout.sql', 'r').read())"

install-container-test:
	docker pull ${CONTAINER}
	docker build -t leapp-tests -f res/docker-tests/Dockerfile res/docker-tests

install-test:
	pip install -r requirements-tests.txt

container-test:
	docker run --rm -ti -v ${PWD}:/payload leapp-tests

test:
	py.test --flake8 --cov-report term-missing --cov=leapp tests/scripts
	py.test --flake8 leapp

.PHONY: install-deps install install-test test
