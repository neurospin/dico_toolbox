# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= python3 -msphinx 
#sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)


install:
	rm -rf _build/doctrees _build/dico_toolbox.github.io
	# first clone the neurospin/dico_toolbox.github.io repo because it may ask
	# for password and we don't want to delay this long build in
	# the middle of it
	# --no-checkout just fetches the root folder without content
	# --depth 1 is a speed optimization since we don't need the
	# history prior to the last commit
	# -b gh-pages fetches only the branch for the gh-pages
	git clone -b gh-pages --single-branch --no-checkout --depth 1 git@github.com:neurospin/dico_toolbox.git _build/dico_toolbox.github.io
	touch _build/dico_toolbox.github.io/.nojekyll
	sphinx-apidoc -o . ../dico_toolbox
	make html
	cd _build/ && \
	cp -r html/* dico_toolbox.github.io && \
	cd dico_toolbox.github.io && \
	git add * && \
	git add .nojekyll && \
	git commit -a -m 'Make install' && \
	git push