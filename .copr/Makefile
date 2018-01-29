MAKE_FILE_DIR := $(realpath $(dir $(firstword $(MAKEFILE_LIST))))

.PHONY: srpm

srpm:
	bash $(MAKE_FILE_DIR)/build.sh $(outdir)
