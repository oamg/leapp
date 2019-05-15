
REPO_PATH := $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
YUM_OR_DNF := $(shell command -v dnf || command -v yum)

install-git:
	@echo --- Installing git if not present ---
	@$(YUM_OR_DNF) install -y /usr/bin/git

srpm:	install-git
	@echo --- Building SRPM ---
	@make -f $(REPO_PATH)/../Makefile srpm
	@mv $(REPO_PATH)/../packaging/SRPMS/*.rpm $(outdir)
	@echo --- Done ---
