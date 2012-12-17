# Makefile for Sphinx documentation
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build2
PAPER         =
BUILDDIR      = _build

# Internal variables
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) source

GH_PAGES_SOURCES = source Makefile
GH_SOURCE_BRANCH = develop

.PHONY: clean html gh-pages

clean:
	-rm -rf $(BUILDDIR)/*

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

gh-pages:
	git checkout gh-pages
	find .. -maxdepth 1 ! -name '.git*' -and ! -name 'docs' -exec rm -rf {} \;
	git checkout ${GH_SOURCE_BRANCH} ${GH_PAGES_SOURCES}
	git reset HEAD
	make html
	mv -fv _build/html/* ..
	rm -rf _build ${GH_PAGES_SOURCES}
	git add ..
	git commit -m "Create gh-pages for '`git log develop -1 --pretty=oneline --abbrev-commit`'"
	git push origin gh-pages
	git checkout ${GH_SOURCE_BRANCH}
