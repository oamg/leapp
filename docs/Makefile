# Minimal makefile for Sphinx documentation
#
## default build operation:
all: clean html

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXAUTOBUILD = sphinx-autobuild
SPHINXPROJ    = Leapp
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@source venv/bin/activate && \
	$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

livehtml:
	@source venv/bin/activate && \
	$(SPHINXAUTOBUILD) --watch ../leapp "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(0)

# Prepare virtualenv similar to the environment used during build on Read The Docs and install required packages
env:
	# ad. pip install -r doesn't really work with relative paths :), so keeping it in the project root
	@PY_VER=$$(sed -n -e 's/^\s*python:\s"\(.*\)"/\1/p' ../.readthedocs.yaml); \
	echo $$PY_VER; \
	rm -fr ./venv; \
	virtualenv venv --python=python$$PY_VER && \
	source venv/bin/activate && \
	pushd .. && pip install -r requirements-docs.txt; popd

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@source venv/bin/activate && \
	$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: all help Makefile env
