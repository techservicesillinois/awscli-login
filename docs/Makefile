DOCSRCS := $(wildcard *.rst *.py ../README.rst)
SRCS := $(patsubst %.py,../%.py,$(SRCS))
TSTS := $(patsubst %.py,../%.py,$(TSTS))

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = build

SPHINXAPIDOC      = sphinx-apidoc
APIDOC_BUILD_DIR  = src
APIDOC_SOURCE_DIR = ../src

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile html doctest clean

html: build/html

doctest: build/doctest/output.txt

$(APIDOC_BUILD_DIR): $(DOCSRCS) $(TSTS) $(SRCS)
	$(SPHINXAPIDOC) -o $(APIDOC_BUILD_DIR) $(APIDOC_SOURCE_DIR)

build/html: $(APIDOC_BUILD_DIR) $(DOCSRCS) $(TSTS) $(SRCS)
	$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

build/doctest/output.txt: $(APIDOC_BUILD_DIR) $(DOCSRCS) $(TSTS) $(SRCS)
	$(SPHINXBUILD) -M doctest "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# This avoids the catch-all target below
%.rst:

# This avoids the catch-all target below
%.py:

## Catch-all target: route all unknown targets to Sphinx using the new
## "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
#	@rm -rf $(APIDOC_BUILD_DIR) $(BUILDDIR)
	@$(SPHINXAPIDOC) -o $(APIDOC_BUILD_DIR) $(APIDOC_SOURCE_DIR)
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	rm -rf $(APIDOC_BUILD_DIR) $(BUILDDIR)
