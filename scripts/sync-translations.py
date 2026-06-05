#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Aaron K. Clark
#
# Re-generate the Spanish and French resumes from the English one (resume.tex
# is the single source of truth). Each run sends the full English LaTeX through
# the Claude CLI (`claude -p`) with strict rules: translate prose only, leave
# every LaTeX command, URL, brand/product/tech name, date, and certification
# untouched. Then it rebuilds the PDFs so you immediately see if anything broke.
#
# Workflow: edit resume.tex -> run this -> review `git diff` + the PDFs -> commit.
# It deliberately does NOT commit or push; translated job material gets a human
# proofread first (even decorative material).
#
# Usage:
#   scripts/sync-translations.py                 # sync es + fr, then build
#   scripts/sync-translations.py es              # just Spanish
#   scripts/sync-translations.py --no-build      # skip the pdflatex step
#
# Requires: `claude` on PATH (Claude CLI). Optional: CLAUDE_MODEL to pin a model.

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "resume.tex"

# Per-language section/label glossary, written with LaTeX escaped-accent macros
# (\'a, \~n, ...) so the output matches the existing files' convention.
GLOSSARIES = {
    "es": {
        "language": "Spanish",
        "terms": [
            "Summary -> Resumen",
            "Selected Open-Source \\& AI Projects -> Proyectos Destacados de C\\'odigo Abierto e IA",
            "Open-Source Contributions -> Contribuciones de C\\'odigo Abierto",
            "Experience -> Experiencia",
            "Technical Strengths -> Competencias T\\'ecnicas",
            "Education -> Educaci\\'on",
            "Volunteer Experience -> Experiencia Voluntaria",
            "Row labels: AI/ML -> IA/ML, Cloud -> Nube, Tools -> Herramientas, "
            "Languages -> Lenguajes, Certifications -> Certificaciones, Memberships -> Membres\\'ias",
            "Remote -> Remoto, Present -> Presente",
        ],
    },
    "fr": {
        "language": "French",
        "terms": [
            "Summary -> R\\'esum\\'e",
            "Selected Open-Source \\& AI Projects -> Projets s\\'electionn\\'es open source et IA",
            "Open-Source Contributions -> Contributions open source",
            "Experience -> Exp\\'erience",
            "Technical Strengths -> Comp\\'etences techniques",
            "Education -> Formation",
            "Volunteer Experience -> B\\'en\\'evolat",
            "Row labels: AI/ML -> IA/ML, Cloud -> Cloud, Tools -> Outils, "
            "Languages -> Langages, Certifications -> Certifications, Memberships -> Adh\\'esions",
            "Remote -> T\\'el\\'etravail, Present -> Pr\\'esent",
            "Use a thin non-breaking space before : ; ! ? as in French typography (the source already uses ~: and ~;).",
        ],
    },
}

# Brand / product / tech names that must survive verbatim. Institutional
# descriptors (Marine Corps, National Guard, University, Volunteer Fire
# Department) MAY be translated; these brand/tech tokens must NOT be.
DO_NOT_TRANSLATE = (
    "KaliMCP, PerplexityAgent, omind, TimeTrackerAPI, hermes-agent, OWASP ZAP, Libation, "
    "Model Context Protocol, MCP, Claude Code, Codex, LangChain, LangGraph, Hugging Face, "
    "OpenAI, Anthropic, Ollama, RAG, pgvector, Pinecone, AWS, Azure, Terraform, Docker, "
    "Kubernetes, Kafka, LogScale, Humio, Burp Suite, Postman, Wireshark, NMap, Datadog, "
    "SumoLogic, NewRelic, CloudFormation, CloudWatch, EC2, S3, RDS, IAM, VPC, ELB, EFS, "
    "Workspaces, ASP.NET, WinForms, AS/400, T-SQL, XML, SAST, EMT-B, USMC, SSCP, CompTIA, "
    "Ronin 48, Black Hills Information Security, Active Countermeasures, CrowdStrike, "
    "CloudHesive, Tmutla, Reinke Manufacturing, Alpine Testing Solutions, Orthman Manufacturing, "
    "Intellicom, Rackspace, Cimarron Software Services, MegaHaus, NASA, WiCyS, Cybershield, "
    "and all university names, person names, email, phone, and \\href{} URLs"
)

PROMPT_TEMPLATE = """You are translating a LaTeX résumé from English to {language}.

Output ONLY the complete translated .tex file content. No explanations, no
preamble, no markdown code fences -- just the raw LaTeX, ready to write to disk.

Hard rules:
1. Translate ONLY natural-language prose: the summary paragraph, the \\item
   bullet descriptions, job titles (e.g. "Senior Developer"), section titles,
   and words like "Remote" and "Present" / month abbreviations.
2. Do NOT translate or alter, in any way: every LaTeX command and environment
   (\\documentclass, \\begin/\\end, \\item, \\href, \\bf, \\needspace, tabular,
   etc.), the entire preamble/package block, all dates, all certification names,
   and these brand/product/tech names -> {dnt}.
3. Keep every \\href{{URL}}{{text}} URL byte-for-byte identical; you may translate
   only the visible {{text}} when it is prose.
4. Use LaTeX escaped-accent macros for ALL accented characters
   (\\'a \\'e \\'i \\'o \\'u \\~n \\`e \\`a \\^o \\c{{c}} etc.). Do NOT emit raw
   accented UTF-8 bytes.
5. Institutional descriptors may be localized the usual way (e.g. United States
   Marine Corps, Army National Guard, Harvard University, Minden Volunteer Fire
   Department), but brand/company names from the list above stay verbatim.
6. Keep the document structure, section order, and number of \\item lines
   identical to the source.
7. Ensure the preamble contains \\usepackage[utf8]{{inputenc}} and
   \\usepackage[T1]{{fontenc}} (add them right after the geometry line if the
   source lacks them) so accents render.

Use these exact translations for section titles and table labels:
{glossary}

Here is the English source to translate:

{source}
"""


def build_prompt(lang: str, source_text: str) -> str:
    g = GLOSSARIES[lang]
    glossary = "\n".join(f"  - {t}" for t in g["terms"])
    return PROMPT_TEMPLATE.format(
        language=g["language"],
        dnt=DO_NOT_TRANSLATE,
        glossary=glossary,
        source=source_text,
    )


def strip_fences(text: str) -> str:
    """Defensively remove ```latex ... ``` wrappers if the model adds them."""
    t = text.strip()
    fence = re.match(r"^```[a-zA-Z]*\n(.*)\n```$", t, flags=re.DOTALL)
    if fence:
        return fence.group(1).strip() + "\n"
    return t + "\n"


def translate(lang: str, source_text: str) -> str:
    prompt = build_prompt(lang, source_text)
    cmd = ["claude", "-p", prompt]
    model = os.environ.get("CLAUDE_MODEL")
    if model:
        cmd[1:1] = ["--model", model]
    print(f"  -> translating to {GLOSSARIES[lang]['language']} via claude ...", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=900)
    if proc.returncode != 0:
        sys.exit(
            f"claude failed for {lang} (exit {proc.returncode}):\n{proc.stderr.strip()}"
        )
    out = strip_fences(proc.stdout)
    if "\\end{document}" not in out:
        sys.exit(
            f"translation for {lang} does not look like a full .tex file "
            f"(no \\end{{document}}). Aborting before overwrite."
        )
    return out


def build_pdfs(langs: list[str]) -> None:
    if not shutil.which("pdflatex"):
        print("pdflatex not found; skipping build.", file=sys.stderr)
        return
    if shutil.which("make"):
        targets = [f"resume_{l}.pdf" for l in langs]
        print(f"  -> building {', '.join(targets)} ...", flush=True)
        r = subprocess.run(
            ["make", *targets], cwd=REPO_ROOT, capture_output=True, text=True, errors="replace"
        )
        if r.returncode != 0:
            sys.exit(f"build failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    else:
        for lang in langs:
            tex = f"resume_{lang}.tex"
            for _ in range(2):  # twice for refs/hyperref
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", tex],
                    cwd=REPO_ROOT, capture_output=True, text=True,
                )


def main() -> None:
    ap = argparse.ArgumentParser(description="Sync es/fr resumes from English resume.tex.")
    ap.add_argument("langs", nargs="*", choices=["es", "fr"], help="languages (default: both)")
    ap.add_argument("--no-build", action="store_true", help="skip the pdflatex build step")
    args = ap.parse_args()

    if not shutil.which("claude"):
        sys.exit("`claude` not found on PATH. Install the Claude CLI to use this script.")
    if not SOURCE.exists():
        sys.exit(f"source not found: {SOURCE}")

    langs = args.langs or ["es", "fr"]
    source_text = SOURCE.read_text(encoding="utf-8")

    print(f"Syncing {', '.join(langs)} from {SOURCE.name} ...")
    for lang in langs:
        out = translate(lang, source_text)
        dest = REPO_ROOT / f"resume_{lang}.tex"
        dest.write_text(out, encoding="utf-8")
        print(f"  wrote {dest.name} ({len(out.splitlines())} lines)")

    if not args.no_build:
        build_pdfs(langs)

    print("\nDone. Review `git diff` and the regenerated PDFs, then commit.")


if __name__ == "__main__":
    main()
