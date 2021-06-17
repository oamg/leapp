# there are bashisms used in this Makefile
SHELL=/bin/bash

PYTHON_VENV ?= python
VENVNAME ?= tut
DIST_VERSION ?= 7
CONFDIR=${DESTDIR}/etc/leapp
LIBDIR=${DESTDIR}/var/lib/leapp

PKGNAME="leapp"
VERSION=`grep -m1 "^Version:" packaging/$(PKGNAME).spec | grep -om1 "[0-9].[0-9.]**"`

# by default use values you can see below, but in case the COPR_* var is defined
# use it instead of the default
_COPR_REPO=$${COPR_REPO:-leapp}
_COPR_CONFIG=$${COPR_CONFIG:-~/.config/copr_rh_oamg.conf}

# just to reduce number of unwanted builds mark as the upstream one when
# someone will call copr_build without additional parameters
MASTER_BRANCH=master

# In case the PR or MR is defined or in case build is not comming from the
# MATER_BRANCH branch, N_REL=0; (so build is not update of the approved
# upstream solution). For upstream builds N_REL=100;
N_REL=`_NR=$${PR:+0}; if test "$${_NR:-100}" == "100"; then _NR=$${MR:+0}; fi; git rev-parse --abbrev-ref HEAD | grep -q "^$(MASTER_BRANCH)$$" || _NR=0;  echo $${_NR:-100}`

TIMESTAMP:=$${__TIMESTAMP:-$(shell /bin/date "+%Y%m%d%H%MZ" -u)}
SHORT_SHA=`git rev-parse --short HEAD`
BRANCH=`git rev-parse --abbrev-ref HEAD | tr -- '-/' '_'`

# In case anyone would like to add any other suffix, just make it possible
_SUFFIX=`if test -n "$$SUFFIX"; then echo ".$${SUFFIX}"; fi; `

# generate empty string if PR or MR are not specified, otherwise set one of them
REQUEST=`if test -n "$$PR"; then echo ".PR$${PR}"; elif test -n "$$MR"; then echo ".MR$${MR}"; fi; `

# replace "custombuild" with some a describing your build
# Examples:
#    0.201810080027Z.4078402.packaging.PR2
#    0.201810080027Z.4078402.packaging
#    0.201810080027Z.4078402.master.MR2
#    1.201810080027Z.4078402.master
RELEASE="$(N_REL).$(TIMESTAMP).$(SHORT_SHA).$(BRANCH)$(REQUEST)$(_SUFFIX)"

ifneq ($(shell id -u),0)
	ENTER_VENV := . $(VENVNAME)/bin/activate;
else
	ENTER_VENV := 
endif

all: help

help:
	@echo "Usage: make <target>"
	@echo
	@echo "Available targets are:"
	@echo "  help                   show this text"
	@echo "  clean                  clean the mess"
	@echo "  prepare                clean the mess and prepare dirs"
	@echo "  print_release          print release how it should look like with"
	@echo "                         with the given parameters"
	@echo "  source                 create the source tarball suitable for"
	@echo "                         packaging"
	@echo "  srpm                   create the SRPM"
	@echo "  copr_build             create the COPR build using the COPR TOKEN"
	@echo "                         - default path is: $(_COPR_CONFIG)"
	@echo "                         - can be changed by the COPR_CONFIG env"
	@echo ""
	@echo "Possible use:"
	@echo "  make <target>"
	@echo "  PR=5 make <target>"
	@echo "  MR=6 <target>"
	@echo "  PR=7 SUFFIX='my_additional_suffix' make <target>"
	@echo "  MR=6 COPR_CONFIG='path/to/the/config/copr/file' <target>"
	@echo ""

clean:
	@echo "--- Clean repo ---"
	@rm -rf packaging/{sources,SRPMS}/
	@rm -rf build/ dist/ *.egg-info
	@find . -name '__pycache__' -exec rm -fr {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +

prepare: clean
	@echo "--- Prepare build directories ---"
	@mkdir -p packaging/{sources,SRPMS}/

source: prepare
	@echo "--- Create source tarball ---"
	@echo git archive --prefix "$(PKGNAME)-$(VERSION)/" -o "packaging/sources/$(PKGNAME)-$(VERSION).tar.gz" HEAD
	@git archive --prefix "$(PKGNAME)-$(VERSION)/" -o "packaging/sources/$(PKGNAME)-$(VERSION).tar.gz" HEAD

srpm: source
	@echo "--- Build SRPM: $(PKGNAME)-$(VERSION)-$(RELEASE).. ---"
	@cp packaging/$(PKGNAME).spec packaging/$(PKGNAME).spec.bak
	@sed -i "s/1%{?dist}/$(RELEASE)%{?dist}/g" packaging/$(PKGNAME).spec
	@rpmbuild -bs packaging/$(PKGNAME).spec \
		--define "_sourcedir `pwd`/packaging/sources"  \
		--define "_srcrpmdir `pwd`/packaging/SRPMS" \
		--define "rhel $(DIST_VERSION)" \
		--define 'dist .el$(DIST_VERSION)' \
		--define 'el$(DIST_VERSION) 1' || FAILED=1
	@mv packaging/$(PKGNAME).spec.bak packaging/$(PKGNAME).spec

copr_build: srpm
	@echo "--- Build RPM ${PKGNAME}-${VERSION}-${RELEASE}.el$(DIST_VERSION).rpm in COPR ---"
	@echo copr-cli --config $(_COPR_CONFIG) build $(_COPR_REPO) \
		packaging/SRPMS/${PKGNAME}-${VERSION}-${RELEASE}*.src.rpm
	@copr-cli --config $(_COPR_CONFIG) build $(_COPR_REPO) \
		packaging/SRPMS/${PKGNAME}-${VERSION}-${RELEASE}*.src.rpm

print_release:
	@echo $(RELEASE)

install-deps:
	pip install -r requirements.txt

install:
	install -dm 0755 ${CONFDIR}
	install -m 0744 etc/leapp/leapp.conf ${CONFDIR}
	install -m 0744 etc/leapp/logger.conf ${CONFDIR}
	install -dm 0755 ${LIBDIR}
	umask 177 && $(PYTHON_VENV) -c "import sqlite3; sqlite3.connect('${LIBDIR}/audit.db').executescript(open('res/audit-layout.sql', 'r').read())"

install-test:
ifeq ($(shell id -u), 0)
	pip install -r requirements-tests.txt
else
	virtualenv --python $(PYTHON_VENV) $(VENVNAME)
	. $(VENVNAME)/bin/activate ; \
	pip install -r requirements-tests.txt
endif


test:   lint
	@ $(ENTER_VENV) \
	pytest -vv --cov-report term-missing --cov=leapp tests/scripts

lint:
	@ $(ENTER_VENV) \
	pytest --cache-clear --pylint -m pylint leapp tests/scripts/*.py; \
	pytest --cache-clear --flake8 -m flake8 leapp tests/scripts/*.py

fast_lint:
	@ $(ENTER_VENV) \
	FILES_TO_LINT="$$(git diff --name-only $(MASTER_BRANCH)| grep '\.py$$')"; \
	if [[ -n "$$FILES_TO_LINT" ]]; then \
		pylint -j 0 $$FILES_TO_LINT && \
		flake8 $$FILES_TO_LINT; \
		LINT_EXIT_CODE="$$?"; \
		if [[ "$$LINT_EXIT_CODE" != "0" ]]; then \
			exit $$LINT_EXIT_CODE; \
		fi; \
		if [[ "$(_PYTHON_VENV)" == "python2.7" ]] ; then \
			pylint --py3k $$FILES_TO_LINT; \
		fi; \
	else \
		echo "No files to lint."; \
	fi

.PHONY: clean copr_build install install-deps install-test srpm test lint fast_lint
