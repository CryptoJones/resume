# Resume for Aaron K. Clark (CryptoJones)

https://raw.githubusercontent.com/CryptoJones/resume/master/resume.pdf

`resume.tex` is the single source of truth. `resume_es.tex` / `resume_fr.tex`
are generated translations (`scripts/sync-translations.py`), and
`resume_en.{tex,pdf}` are symlinks to `resume.{tex,pdf}`.

## Build everything

```sh
scripts/generate.py          # all languages (en/es/fr) x all formats (pdf/md)
scripts/generate.py --sync   # re-translate es/fr from English first, then build
```

Requires `pdflatex` and `pandoc` 3.x (`--sync` additionally needs the Claude
CLI).

## PDF pipeline (pdflatex)

```sh
make pdf            # resume.pdf, resume_es.pdf, resume_fr.pdf
make resume.pdf     # a single document
```

Each `.tex` is compiled twice with `pdflatex -interaction=nonstopmode` against
the custom `resume.cls` (twice so cross-references settle).

## Markdown pipeline (pandoc)

```sh
make md             # resume.md, resume_es.md, resume_fr.md
make resume.md      # a single document
```

Pandoc never reads `resume.cls`, so the rule prepends
`scripts/pandoc-defs.tex`, which maps the custom constructs (`\name`,
`\address`, `rSection`, `rSubsection`) onto standard LaTeX the reader
understands:

```sh
pandoc scripts/pandoc-defs.tex resume.tex -f latex -t gfm \
    --lua-filter=scripts/resume-md.lua --wrap=none -o resume.md
```

`scripts/resume-md.lua` then rebuilds the name/contact header (pandoc drops
preamble content, so `\name`/`\address` travel as title/author metadata) and
collapses each job's dates/role/location into one italic meta line.

## Housekeeping

```sh
make            # = make pdf md
make clean      # LaTeX build artifacts
make distclean  # also the generated .pdf/.md files
```
