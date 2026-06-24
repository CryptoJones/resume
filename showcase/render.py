#!/usr/bin/env python3
"""Render the Cyberdeck code-showcase HTML from the scrubbed samples.

Pipeline position: gather.py -> [render.py] -> Chrome --print-to-pdf -> raster.

Each project gets an intro page (plain-language explanation, then chips) followed
by one or more code pages. Code is highlighted with a custom Cyberdeck Pygments
style and paginated on blank-line boundaries so a page rarely breaks mid-block.
The on-theme anti-OCR layers (scanlines, grain, glyph-warp, watermark) live in
cyberdeck.css and the inline SVG filter below."""

import html
import os

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.style import Style
from pygments.token import (Comment, Error, Generic, Keyword, Name, Number,
                            Operator, Punctuation, String, Token)

from manifest import AUTHOR, PROJECTS

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "samples")
MAX_LINES = 55          # clip-safe lines per code page at 10.5px / 1.36


class Cyberdeck(Style):
    """Dark-neon token palette matching the Cyberdeck theme."""
    background_color = "#0a0e16"
    styles = {
        Token:              "#c6d2e2",
        Comment:            "italic #5a6678",
        Comment.Preproc:    "#ff8f6a",
        Keyword:            "bold #27d4ff",
        Keyword.Type:       "#27d4ff",
        Operator:           "#9fb0c4",
        Punctuation:        "#9fb0c4",
        Name:               "#c6d2e2",
        Name.Function:      "#55ff99",
        Name.Class:         "bold #ffb454",
        Name.Namespace:     "#ffb454",
        Name.Decorator:     "#ff8f6a",
        Name.Builtin:       "#b48cff",
        Name.Attribute:     "#9fe6c2",
        Name.Constant:      "#ffb454",
        Name.Tag:           "#27d4ff",
        String:             "#8ef0b0",
        String.Doc:         "italic #6f9a7e",
        String.Escape:      "#ffb454",
        Number:             "#ffb454",
        Generic.Heading:    "#27d4ff",
        Error:              "#ff4f4f",
    }


FORMATTER = HtmlFormatter(style=Cyberdeck, nowrap=True)


def lexer_for(lang):
    try:
        return get_lexer_by_name(lang)
    except Exception:
        # GDScript on older Pygments: fall back to a python-ish highlight.
        return get_lexer_by_name("python")


def paginate(lines):
    """Split into the fewest pages needed, balanced evenly so there are no
    orphan/near-empty trailing pages (e.g. a 58-line file becomes 29+29, not
    52+6)."""
    n = len(lines)
    npages = max(1, -(-n // MAX_LINES))   # ceil division
    per = -(-n // npages)                 # balanced lines per page
    return [lines[i:i + per] for i in range(0, n, per)]


def code_block(lang, text):
    lx = lexer_for(lang)
    inner = highlight(text, lx, FORMATTER)
    return f'<div class="highlight"><pre class="code">{inner}</pre></div>'


def overlays():
    return '<div class="watermark"></div>'


def page(cls, body):
    return f'<section class="page {cls}">{overlays()}{body}</section>'


def title_page():
    langs = "Rust · Go · Python · JavaScript · SQL · C# · GDScript"
    body = f"""
      <div class="deck">Selected Work</div>
      <h1>Code&nbsp;Samples</h1>
      <div class="sub">A curated showcase of original engineering work.</div>
      <div class="rule"></div>
      <div class="meta">
        {html.escape(AUTHOR)}<br>
        Six original projects · seven languages<br>
        {langs}
      </div>
    """
    return page("title-page", body)


def intro_page(proj):
    chips = "".join(
        f'<span class="chip {kind}">{html.escape(label)}</span>'
        for label, kind in proj["chips"]
    )
    body = f"""
      <div class="kicker">Project</div>
      <h2>{html.escape(proj['name'])}</h2>
      <div class="tagline">{html.escape(proj['tagline'])}</div>
      <div class="blurb">{html.escape(proj['blurb'])}</div>
      <div class="chips">{chips}</div>
    """
    return page("intro", body)


def code_pages(proj):
    out = []
    for s in proj["samples"]:
        path = os.path.join(SAMPLES, f"{s['id']}.{s['ext']}")
        with open(path, encoding="utf-8") as fh:
            lines = fh.readlines()
        chunks = paginate(lines)
        total = len(chunks)
        for idx, chunk in enumerate(chunks, 1):
            part = f' <span class="lang">part {idx}/{total}</span>' if total > 1 else \
                   f' <span class="lang">{s["lang"]}</span>'
            cap = (f'<div class="caption"><span class="fname">{html.escape(s["fname"])}</span>'
                   f'{part}<br>{html.escape(s["what"])}</div>')
            block = code_block(s["lang"], "".join(chunk))
            out.append(page("code-page", cap + f'<div class="code-wrap">{block}</div>'))
    return out


def build():
    with open(os.path.join(HERE, "cyberdeck.css"), encoding="utf-8") as fh:
        css = fh.read()
    pyg_css = FORMATTER.get_style_defs(".highlight")

    pages = [title_page()]
    for proj in PROJECTS:
        pages.append(intro_page(proj))
        pages.extend(code_pages(proj))

    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Code Samples</title>
<style>
{css}
{pyg_css}
</style></head>
<body>
{"".join(pages)}
</body></html>"""

    out = os.path.join(HERE, "showcase.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"render: wrote {out} ({len(pages)} pages)")


if __name__ == "__main__":
    build()
