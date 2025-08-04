# there are bashisms used in this Makefile
SHELL=/bin/bash

PYTHON_VENV ?= python
VENVNAME ?= tut
DIST_VERSION ?= 8
CONFDIR=${DESTDIR}/etc/leapp
LIBDIR=${DESTDIR}/var/lib/leapp

PKGNAME="leapp"
VERSION=`grep -m1 "^Version:" packaging/$(PKGNAME).spec | grep -om1 "[0-9].[0-9.]**"`

# by default use values you can see below, but in case the COPR_* var is defined
# use it instead of the default
_COPR_REPO=$${COPR_REPO:-leapp}
_COPR_CONFIG=$${COPR_CONFIG:-~/.config/copr_rh_oamg.conf}

# tool used to run containers for testing and building packages
_CONTAINER_TOOL=$${CONTAINER_TOOL:-podman}

# container used to run unit tests
_TEST_CONTAINER=$${TEST_CONTAINER:-rhel8}

# just to reduce number of unwanted builds mark as the upstream one when
# someone will call copr_build without additional parameters
MASTER_BRANCH=main

# In case the PR or MR is defined or in case build is not coming from the
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
#    0.201810080027Z.4078402.main.MR2
#    1.201810080027Z.4078402.main
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
	@echo "  install-test           installs test dependencies"
	@echo "  test                   runs linter and unit tests"
	@echo "  test_container         runs linter and unit tests in a container"
	@echo "                         - by default rhel8 container is used"
	@echo "                         - can be changed by setting TEST_CONTAINER env variable"
	@echo "                         - available containers are:" rhel{8..10}
	@echo "  test_container_all     runs linter and tests in all available containers"
	@echo "  lint                   runs just the linter"
	@echo "  build                  create the RPM"
	@echo "  build_container        create the RPM in container"
	@echo "                         - set BUILD_CONTAINER to select the container"
	@echo "                         - available containers are:" el{8..9} f{35..40} rawhide
	@echo "                         - this can't be used to build in parallel,"
	@echo "                           as build containers operate on the same files"
	@echo "  clean_containers      clean container images used for building"
	@echo ""
	@echo "Possible use:"
	@echo "  make <target>"
	@echo "  PR=5 make <target>"
	@echo "  MR=6 <target>"
	@echo "  PR=7 SUFFIX='my_additional_suffix' make <target>"
	@echo "  MR=6 COPR_CONFIG='path/to/the/config/copr/file' <target>"
	@echo "  TEST_CONTAINER=rhel8 make test_container"
	@echo "  BUILD_CONTAINER=el8 make build_container"
	@echo "  CONTAINER_TOOL=docker make test_container"
	@echo ""

clean:
	@echo "--- Clean repo ---"
	@rm -rf packaging/{sources,SRPMS,BUILD,BUILDROOT,RPMS}/
	@rm -rf build/ dist/ *.egg-info
	@find . -name '__pycache__' -exec rm -fr {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +

prepare: clean
	@echo "--- Prepare build directories ---"
	@mkdir -p packaging/{sources,SRPMS,BUILD,BUILDROOT,RPMS}/

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

build: source
	@echo "--- Build RPM ${PKGNAME}-${VERSION}-${RELEASE}.el$(DIST_VERSION).rpm ---"
	@cp packaging/$(PKGNAME).spec packaging/$(PKGNAME).spec.bak
	@sed -i "s/1%{?dist}/$(RELEASE)%{?dist}/g" packaging/$(PKGNAME).spec
	@rpmbuild -ba packaging/$(PKGNAME).spec \
		--define "_sourcedir `pwd`/packaging/sources"  \
		--define "_srcrpmdir `pwd`/packaging/SRPMS" \
		--define "_builddir `pwd`/packaging/BUILD" \
		--define "_buildrootdir `pwd`/packaging/BUILDROOT" \
		--define "_rpmdir `pwd`/packaging/RPMS" \
		--define "rhel $(DIST_VERSION)" \
		--define 'dist .el$(DIST_VERSION)' \
		--define 'el$(DIST_VERSION) 1' || FAILED=1
	@mv packaging/$(PKGNAME).spec.bak packaging/$(PKGNAME).spec

build_container:
	@case "$$BUILD_CONTAINER" in \
	el[8-9]) \
		_CONT_FILE="Containerfile.ubi"$${BUILD_CONTAINER: -1}; \
		;; \
	f3[5-9]|f40|rawhide) \
		[ $$BUILD_CONTAINER = rawhide ] && VERSION=latest || VERSION=$${BUILD_CONTAINER: -2}; \
		_CONT_FILE=".Containerfile.$${BUILD_CONTAINER}"; \
		cp res/container-builds/Containerfile.fedora_generic res/container-builds/$$_CONT_FILE && \
		sed -i "1i FROM fedora:$${VERSION}" res/container-builds/$$_CONT_FILE \
		;; \
	"") \
		echo "BUILD_CONTAINER must be set"; \
		exit 1; \
		;; \
	*) \
		echo "Available containers are: el{8..9} f{35..40} rawhide"; \
		exit 1; \
		;; \
	esac && \
	echo "--- Preparing $$BUILD_CONTAINER container for building ---" && \
	IMAGE_NAME="leapp-build-$${BUILD_CONTAINER}"; \
	$(_CONTAINER_TOOL) build -f res/container-builds/$$_CONT_FILE -t $$IMAGE_NAME res/container-builds/ && \
	$(_CONTAINER_TOOL) run --rm -v $$PWD:/payload:Z --name "$${IMAGE_NAME}-cont" $$IMAGE_NAME && \
	[ '$${_CONT_FILE:0:1}' = '.' ] && rm -f res/container-builds/$$_CONT_FILE || :

print_release:
	@echo $(RELEASE)

install-deps:
	@ $(ENTER_VENV) \
	pip install -r requirements.txt

install:
	install -dm 0755 ${CONFDIR}
	install -m 0744 etc/leapp/leapp.conf ${CONFDIR}
	install -m 0744 etc/leapp/logger.conf ${CONFDIR}
	install -dm 0700 ${LIBDIR}
	umask 177 && $(PYTHON_VENV) -c "import sqlite3; sqlite3.connect('${LIBDIR}/audit.db').executescript(open('res/audit-layout.sql', 'r').read())"

install-test:
ifeq ($(shell id -u), 0)
	pip install -r requirements-tests.txt
else
	virtualenv --python $(PYTHON_VENV) $(VENVNAME)
	. $(VENVNAME)/bin/activate ; \
	pip install -r requirements-tests.txt
endif

test: lint
	@ $(ENTER_VENV) \
	pytest -vv --cov-report term-missing --cov=leapp tests/scripts

# TODO(pstodulk): create ticket to add rhel10 for testing.... py: 3.12
test_container:
	@case $(_TEST_CONTAINER) in \
		rhel8) \
			export _VENV=python3.6; \
			export _CONT_FILE="res/container-tests/Containerfile.ubi8"; \
			;; \
		rhel9) \
			export _VENV=python3.9; \
			export _CONT_FILE="res/container-tests/Containerfile.ubi9"; \
			;; \
		# TODO the container is currently built on top of RHEL 9 UBI with python3.12 virtualenv \
		rhel10) \
			export _VENV=python3.12; \
			export _CONT_FILE="res/container-tests/Containerfile.ubi10"; \
			;; \
		*) \
			echo "Available test containers are: rhel{8..10}"; \
			exit 1; \
			;; \
	esac; \
	export TEST_IMAGE="leapp-tests-$(_TEST_CONTAINER)"; \
	rm -rf testenv/ && \
	$(_CONTAINER_TOOL) build -t $$TEST_IMAGE -f $$_CONT_FILE res/container-tests && \
	$(_CONTAINER_TOOL) run --rm -v $${PWD}:/payload:Z -e PYTHON_VENV=$$_VENV $$TEST_IMAGE

test_container_all:
	@for container in "rhel"{8..10}; do \
		TEST_CONTAINER=$$container $(MAKE) test_container; \
	done

clean_containers:
	@for i in "leapp-build-"{el8,el9,f35,f36,rawhide} "leapp-tests-rhel"{8..10}; do \
		[ -z $$($(_CONTAINER_TOOL) images -q "$$i") ] || \
		$(_CONTAINER_TOOL) rmi "$$i" > /dev/null 2>&1 || :; \
	done

lint:
	@ $(ENTER_VENV) \
	LINTABLES="$$(find . -name '*.py' | grep -E -e '^\./leapp\/' -e '^\./tests/scripts/' | sort -u )"; \
	echo '==================================================' && \
	echo '==================================================' && \
	echo '===============   Running pylint   ===============' && \
	echo '==================================================' && \
	echo '==================================================' && \
	[[ "$(_PYTHON_VENV)" == "python3.6" ]] && echo "$$LINTABLES" | xargs pylint --py3k || echo "$$LINTABLES" | xargs pylint && echo '===> pylint PASSED' && \
	echo '==================================================' && \
	echo '==================================================' && \
	echo '===============   Running flake8   ===============' && \
	echo '==================================================' && \
	echo '==================================================' && \
	echo "$$LINTABLES" | xargs flake8 && echo '===> flake8 PASSED';

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
		if [[ "$(_PYTHON_VENV)" == "python3.6" ]] ; then \
			pylint --py3k $$FILES_TO_LINT; \
		fi; \
	else \
		echo "No files to lint."; \
	fi

.PHONY: clean copr_build build build_container install install-deps install-test srpm test test_container test_container_all lint fast_lint clean_containers
