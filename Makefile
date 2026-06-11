LATEX    = pdflatex
FLAGS    = -interaction=nonstopmode
PANDOC   = pandoc
PANDOC_DEFS   = scripts/pandoc-defs.tex
PANDOC_FILTER = scripts/resume-md.lua
TARGETS  = resume resume_es resume_fr

all: pdf md

pdf: $(TARGETS:%=%.pdf)

md: $(TARGETS:%=%.md)

%.pdf: %.tex resume.cls
	$(LATEX) $(FLAGS) $<
	$(LATEX) $(FLAGS) $<

# Markdown export: pandoc can't read resume.cls, so pandoc-defs.tex maps the
# custom constructs onto standard LaTeX first and resume-md.lua tidies the
# result (contact header, per-job meta lines).
%.md: %.tex $(PANDOC_DEFS) $(PANDOC_FILTER)
	$(PANDOC) $(PANDOC_DEFS) $< -f latex -t gfm --lua-filter=$(PANDOC_FILTER) --wrap=none -o $@

clean:
	rm -f $(TARGETS:%=%.aux) $(TARGETS:%=%.log) $(TARGETS:%=%.out) \
	      $(TARGETS:%=%.fls) $(TARGETS:%=%.fdb_latexmk) *.synctex.gz

distclean: clean
	rm -f $(TARGETS:%=%.pdf) $(TARGETS:%=%.md)

.PHONY: all pdf md clean distclean
