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
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
livehtml:
	@$(SPHINXAUTOBUILD) --watch ../leapp "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(0)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: all help Makefile
