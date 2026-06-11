#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aaron K. Clark
#
# Build every resume deliverable: each language (en, es, fr) in each format
# (pdf, md). A thin orchestrator over the Makefile, which stays the single
# source of truth for the actual build rules; this just runs every
# language/format pair, collects pass/fail, and prints a summary.
#
# resume_en.{tex,pdf} are symlinks to resume.{tex,pdf}, so building `resume`
# covers English. coverletter.tex is a separate document and not built here.
#
# Usage:
#   scripts/generate.py            # build all languages in all formats
#   scripts/generate.py --sync     # re-translate es/fr from English first
#
# Requires: pdflatex (PDF), pandoc 3.x (Markdown); --sync additionally needs
# the Claude CLI (see scripts/sync-translations.py).

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = ["resume", "resume_es", "resume_fr"]
FORMATS = ["pdf", "md"]


def build(target: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["make", target],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build all resume languages in all formats."
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="re-generate the es/fr translations from resume.tex first",
    )
    args = parser.parse_args()

    if args.sync:
        print("==> syncing translations from resume.tex")
        sync = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "sync-translations.py"),
             "--no-build"],
            cwd=REPO_ROOT,
        )
        if sync.returncode != 0:
            print("translation sync failed; aborting before build", file=sys.stderr)
            return sync.returncode

    failures: list[tuple[str, subprocess.CompletedProcess]] = []
    for doc in DOCS:
        for fmt in FORMATS:
            target = f"{doc}.{fmt}"
            print(f"==> {target} ... ", end="", flush=True)
            proc = build(target)
            if proc.returncode == 0:
                print("ok")
            else:
                print("FAILED")
                failures.append((target, proc))

    print()
    total = len(DOCS) * len(FORMATS)
    print(f"{total - len(failures)}/{total} targets built")
    for target, proc in failures:
        tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-15:])
        print(f"\n--- {target} ---\n{tail}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
