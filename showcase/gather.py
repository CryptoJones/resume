#!/usr/bin/env python3
"""Copy each manifest sample's line range out of its source repo, scrub it, and
write samples/<id>.<ext>. Scrubbing drops license headers, URLs, emails, contact
lines, and the Nebraska/Go Big Red/xkcd tagline. Aborts loudly if any forbidden
token survives, so a bad sample can never reach the PDF."""

import os
import re
import sys

from manifest import PROJECTS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "samples")

URL_RE = re.compile(r"https?://|www\.", re.I)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
TAGLINE_RE = re.compile(r"nebraska|go big red|xkcd", re.I)
HEADER_DROP_RE = re.compile(r"SPDX-License-Identifier|^\s*[-/#]*\s*Copyright\b", re.I)


def scrub(lines):
    """Drop license-header / URL / email / tagline lines. Returns kept lines."""
    kept = []
    for ln in lines:
        if HEADER_DROP_RE.search(ln):
            continue
        if URL_RE.search(ln) or EMAIL_RE.search(ln) or TAGLINE_RE.search(ln):
            continue
        kept.append(ln)
    # trim leading/trailing blank lines left by header removal
    while kept and not kept[0].strip():
        kept.pop(0)
    while kept and not kept[-1].strip():
        kept.pop()
    return kept


def main():
    os.makedirs(OUT, exist_ok=True)
    failures = []
    for proj in PROJECTS:
        for s in proj["samples"]:
            src = s["src"]
            if not os.path.exists(src):
                failures.append(f"MISSING SOURCE: {src}")
                continue
            with open(src, encoding="utf-8") as fh:
                alllines = fh.readlines()
            chunk = alllines[s["start"] - 1 : s["end"]]
            chunk = scrub(chunk)
            text = "".join(chunk).rstrip("\n") + "\n"
            # final safety net
            if URL_RE.search(text) or EMAIL_RE.search(text) or TAGLINE_RE.search(text):
                failures.append(f"FORBIDDEN TOKEN SURVIVED in {s['id']}")
            dest = os.path.join(OUT, f"{s['id']}.{s['ext']}")
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"  wrote {os.path.basename(dest)} ({len(chunk)} lines)")
    if failures:
        print("\nGATHER FAILED:", file=sys.stderr)
        for f in failures:
            print("  " + f, file=sys.stderr)
        sys.exit(1)
    print("gather: ok")


if __name__ == "__main__":
    main()
