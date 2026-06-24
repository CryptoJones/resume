"""Showcase manifest: projects, plain-language intros, and the source excerpts.

Each sample names a real source file and a line range; gather.py copies that
range out, strips license/URL/contact/tagline lines, and writes it to
samples/<id>.<ext>. render.py turns the whole thing into the Cyberdeck HTML.

Hard rules (enforced by gather.py's scrub): no URLs, no emails, no contact
details, no "Nebraska / Go Big Red / xkcd" anywhere in the shown code.
"""

import os

REPOS = "/Users/akclark/source/repos"
SCRATCH = os.environ.get(
    "SHOWCASE_SCRATCH",
    "/private/tmp/claude-501/-Users-akclark-source-repos-resume/"
    "8c84277f-ecba-4ffb-b1b9-86b3926919a1/scratchpad",
)

# title-page author identity (a name is identity, not contact info)
AUTHOR = "Aaron K. Clark"

PROJECTS = [
    {
        "name": "Scylla",
        "tagline": "A reverse-engineering platform with a durable core and disposable heads.",
        "blurb": (
            "A hexagonal RE platform: a durable reverse-engineering domain core "
            "surrounded by swappable protocol “heads” (MCP first). The core never "
            "depends on a head, so the interface can be replaced without touching the "
            "analysis logic. The sample is the submit→poll job handle that runs a "
            "long analysis on a background task — a 200 MB firmware analysis can’t "
            "block the caller — with truthful status and exactly-once result delivery."
        ),
        "chips": [("Rust", "lang"), ("Async / Tokio", "lang"), ("Hexagonal architecture", "role"), ("Architect & author", "role")],
        "samples": [
            {"id": "scylla-job", "ext": "rs", "lang": "rust",
             "src": f"{REPOS}/Scylla/crates/scylla-engine/src/job.rs",
             "start": 1, "end": 97,
             "fname": "scylla-engine/src/job.rs",
             "what": "An async submit→poll job handle: type-safe lifecycle, atomic IDs, and one-shot result semantics for background analysis."},
        ],
    },
    {
        "name": "AdmiralBBS",
        "tagline": "A security-hardened, clean-room reimplementation of a 1990s ANSI BBS.",
        "blurb": (
            "A from-scratch BBS server written in memory-safe Go. The memory-safe "
            "language removes the buffer-overflow bug class; this layer removes the "
            "other one that matters for a terminal service — control-character and "
            "ANSI-escape injection. The sample is the input security boundary: a pure, "
            "fuzzable function that length-bounds and sanitizes everything a caller "
            "sends before it can reach a parser or be echoed to a terminal."
        ),
        "chips": [("Go", "lang"), ("Security hardening", "role"), ("Clean-room", "role")],
        "samples": [
            {"id": "admiralbbs-input", "ext": "go", "lang": "go",
             "src": f"{REPOS}/AdmiralBBS/src/session/input.go",
             "start": 1, "end": 58,
             "fname": "src/session/input.go",
             "what": "A pure, fuzz-testable sanitizer that strips control bytes and ANSI/CSI escape sequences — the service’s injection boundary."},
        ],
    },
    {
        "name": "TimeTrackerAPI",
        "tagline": "An open-source Node.js + PostgreSQL rewrite of a commercial time-tracking API.",
        "blurb": (
            "A multi-tenant REST API with API-key authentication. Two samples from one "
            "project, in two languages: the auth middleware that hashes the incoming "
            "key before lookup and scopes every request to its company, and the "
            "hand-authored Postgres schema — documented conventions, soft-delete, and "
            "partial indexes tuned to the hot read paths."
        ),
        "chips": [("JavaScript / Node", "lang"), ("PostgreSQL / SQL", "lang"), ("REST", "role"), ("Multi-tenant", "role")],
        "samples": [
            {"id": "timetracker-auth", "ext": "js", "lang": "javascript",
             "src": f"{REPOS}/TimeTrackerAPI/app/middleware/auth.js",
             "start": 60, "end": 124,
             "fname": "app/middleware/auth.js",
             "what": "API-key auth: SHA-256 hashed-key lookup through the model layer, with company-scoped access control and fail-closed errors."},
            {"id": "timetracker-schema", "ext": "sql", "lang": "sql",
             "src": f"{REPOS}/TimeTrackerAPI/setup/TimeEntry.sql",
             "start": 3, "end": 43,
             "fname": "setup/TimeEntry.sql",
             "what": "A documented multi-tenant table: schema conventions, soft-delete columns, and partial indexes matched to the listing queries."},
        ],
    },
    {
        "name": "OSApplyTrack",
        "tagline": "An open-source job-search application tracker, running in production.",
        "blurb": (
            "An ASP.NET / .NET API for tracking job applications and generating "
            "materials. The sample is the cover-letter drafter: it builds a strict, "
            "structured LLM prompt from the tenant’s own résumé (not hardcoded facts), "
            "forbids invented claims, and validates the model’s output before it is "
            "ever persisted — dependency-injected and unit-testable."
        ),
        "chips": [("C#", "lang"), ("ASP.NET / .NET", "lang"), ("LLM integration", "role")],
        "samples": [
            {"id": "osapplytrack-drafter", "ext": "cs", "lang": "csharp",
             "src": f"{REPOS}/OSApplyTrack/api/ApplyTrack.Api/Materials/CoverLetterDrafter.cs",
             "start": 3, "end": 88,
             "fname": "Materials/CoverLetterDrafter.cs",
             "what": "An injectable service that builds an anti-hallucination LLM prompt from structured data and validates output before saving."},
        ],
    },
    {
        "name": "XSpaceWar-AI",
        "tagline": "A modern, AI-driven networked reimagining of the classic Spacewar!",
        "blurb": (
            "A Godot 4 multiplayer space-fighter with deterministic, host-authoritative "
            "netcode — clients rebuild the arena from a shared seed and apply snapshots "
            "on top. The sample is the wire protocol: a versioned schema guarded by a "
            "strict equality check (the only thing standing between mixed builds and "
            "silent desync) and authoritative input validation that keeps injection and "
            "junk glyphs out of every scoreboard."
        ),
        "chips": [("GDScript", "lang"), ("Godot 4", "lang"), ("Deterministic netcode", "role"), ("Game dev", "role")],
        "samples": [
            {"id": "xspacewar-protocol", "ext": "gd", "lang": "gdscript",
             "src": f"{SCRATCH}/XSpaceWar-AI/src/net/net_protocol.gd",
             "start": 1, "end": 66,
             "fname": "src/net/net_protocol.gd",
             "what": "Host-authoritative wire protocol: a versioned message schema, safe (object-free) encoding, and defensive callsign validation."},
        ],
    },
    {
        "name": "embed-clamp",
        "tagline": "A pure-stdlib proxy that keeps a fixed-context embedder from choking on big RAG chunks.",
        "blurb": (
            "A transparent, token-aware proxy for OpenAI-compatible embedding servers: "
            "small inputs pass straight through; oversized ones are split to a calibrated "
            "token budget, embedded piecewise, and pooled back into one vector — so a "
            "fixed-context local embedder never errors on a large document. Zero "
            "dependencies. The sample is the splitter and pooling math."
        ),
        "chips": [("Python", "lang"), ("Pure stdlib", "role"), ("RAG / embeddings", "role")],
        "samples": [
            {"id": "embedclamp-core", "ext": "py", "lang": "python",
             "src": f"{REPOS}/embed-clamp/embed_clamp.py",
             "start": 59, "end": 125,
             "fname": "embed_clamp.py",
             "what": "Calibrated token-budget splitting (O(pieces) token calls, not O(lines)) and mean/max vector pooling — dependency-free."},
        ],
    },
]
