LATEX    = pdflatex
FLAGS    = -interaction=nonstopmode
TARGETS  = resume resume_es resume_fr

all: $(TARGETS:%=%.pdf)

%.pdf: %.tex resume.cls
	$(LATEX) $(FLAGS) $<
	$(LATEX) $(FLAGS) $<

clean:
	rm -f $(TARGETS:%=%.aux) $(TARGETS:%=%.log) $(TARGETS:%=%.out) \
	      $(TARGETS:%=%.fls) $(TARGETS:%=%.fdb_latexmk) *.synctex.gz

distclean: clean
	rm -f $(TARGETS:%=%.pdf)

.PHONY: all clean distclean
