# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
scaffold-bundle.py — Scaffold a ticket-writing bundle directory.

Creates `{shared_folder}/tickets/{slug}/` containing four mandatory files:
  - ticket-YYYY-MM-DD-{slug}.md       (kind: ticket,    status: draft)
  - research-YYYY-MM-DD-{slug}.md     (kind: research,  status: active)
  - questions-YYYY-MM-DD-{slug}.md    (kind: questions, status: active)
  - worklog-YYYY-MM-DD-{slug}.md      (kind: worklog,   status: active)

All frontmatter fields are populated from `thoughts metadata` (date, owner,
git_commit, branch, repository, shared_folder) plus the caller's domain args
(topic, slug, primary-tag).

This script is invoked by the ticket-orient skill (step 6: scaffold) once
the user has confirmed scope and the primary tag is locked.

Usage:
    uv run scaffold-bundle.py --topic <str> --slug <str> --primary-tag <tag>

Arguments:
    --topic         Human-readable topic (becomes `topic:` frontmatter field)
    --slug          kebab-case slug (becomes part of filenames + aliases)
    --primary-tag   One of: feature | bug | exploration | hotfix | infrastructure | chore

Exit codes:
    0  Success
    1  Validation error (bad args, invalid primary-tag, slug collision)
    2  Environment error (thoughts CLI not on PATH, metadata parse failed)

Output (stdout): JSON object with the three created file paths, suitable for
the calling skill to capture and pass to subsequent steps:
    {
      "bundle_dir": "/.../tickets/team-workspaces",
      "ticket": "/.../tickets/team-workspaces/ticket-2026-05-17-team-workspaces.md",
      "research": "/.../tickets/team-workspaces/research-2026-05-17-team-workspaces.md",
      "questions": "/.../tickets/team-workspaces/questions-2026-05-17-team-workspaces.md",
      "worklog": "/.../tickets/team-workspaces/worklog-2026-05-17-team-workspaces.md"
    }
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date as date_type
from pathlib import Path
from typing import Any

import yaml

VALID_PRIMARY_TAGS = {
    "feature",
    "bug",
    "exploration",
    "hotfix",
    "infrastructure",
    "chore",
}

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")


def die(msg: str, code: int = 1) -> None:
    """Print an error to stderr and exit."""
    print(f"scaffold-bundle: {msg}", file=sys.stderr)
    sys.exit(code)


def run_thoughts_metadata() -> dict[str, Any]:
    """Run `thoughts metadata` and parse the YAML-like output into a dict.

    The thoughts CLI emits a mixed document with comments and key/value lines.
    We parse line-by-line, ignoring comment lines and section headers, keeping
    only `key: value` pairs where value is a scalar.
    """
    try:
        proc = subprocess.run(
            ["thoughts", "metadata"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        die(
            "`thoughts` CLI not found on PATH. Install thoughts-cli or run `thoughts init` "
            "in the current repository.",
            code=2,
        )
    except subprocess.CalledProcessError as exc:
        die(
            f"`thoughts metadata` failed (exit {exc.returncode}). Stderr: {exc.stderr.strip()}",
            code=2,
        )

    meta: dict[str, Any] = {}
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        # Skip schema/usage hint lines (values starting with "<" describe types).
        if value.startswith("<") or "|" in value:
            continue
        if not value:
            continue
        meta[key] = value

    required = ("date", "owner", "git_commit", "branch", "repository", "shared_folder")
    missing = [k for k in required if k not in meta]
    if missing:
        die(
            f"`thoughts metadata` output is missing required keys: {', '.join(missing)}. "
            "Run `thoughts metadata` manually to inspect.",
            code=2,
        )
    return meta


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold a ticket-writing bundle directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Human-readable topic for the ticket (free text).",
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="kebab-case slug, used in filenames and aliases.",
    )
    parser.add_argument(
        "--primary-tag",
        required=True,
        choices=sorted(VALID_PRIMARY_TAGS),
        help="Primary tag that drives the depth recipe.",
    )
    return parser.parse_args()


def validate_slug(slug: str) -> None:
    if not SLUG_RE.match(slug):
        die(
            f"Slug {slug!r} is invalid. Use lowercase letters, digits, and single hyphens; "
            "start and end with an alphanumeric character (e.g., `team-workspaces`)."
        )


def short_date(iso_or_date: str) -> str:
    """Extract YYYY-MM-DD from an ISO 8601 timestamp or pass through a date."""
    if len(iso_or_date) >= 10 and iso_or_date[4] == "-" and iso_or_date[7] == "-":
        return iso_or_date[:10]
    die(f"Cannot extract date from {iso_or_date!r} (expected ISO 8601 prefix).", code=2)
    return ""  # unreachable; satisfies type checker


def emit_frontmatter(fm: dict[str, Any]) -> str:
    """Render a frontmatter dict as `---\\n...---\\n` with stable key order."""
    body = yaml.safe_dump(
        fm,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=120,
    )
    return f"---\n{body}---\n"


def build_ticket_frontmatter(
    meta: dict[str, Any],
    topic: str,
    slug: str,
    primary_tag: str,
    research_alias: str,
    questions_alias: str,
    worklog_alias: str,
    canonical_alias: str,
) -> dict[str, Any]:
    # Both `owner` (schema-required) and `researcher` (legacy convention) are
    # populated from `thoughts metadata` → `owner`. `last_updated` uses the
    # full ISO 8601 timestamp from `date` so `thoughts validate` passes.
    return {
        "date": meta["date"],
        "owner": meta["owner"],
        "researcher": meta["owner"],
        "git_commit": meta["git_commit"],
        "branch": meta["branch"],
        "repository": meta["repository"],
        "topic": topic,
        "tags": [primary_tag],
        "status": "draft",
        "last_updated": meta["date"],
        "last_updated_by": meta["owner"],
        "last_updated_note": "Initial bundle scaffolded by ticketsmith.",
        "aliases": [canonical_alias, slug],
        "kind": "ticket",
        "schema_version": 1,
        "source": "manual",
        "assignee": meta["owner"],
        "priority": 2,
        "depends_on": [],
        "blocks": [],
        "children": [f"[[{research_alias}]]", f"[[{questions_alias}]]", f"[[{worklog_alias}]]"],
    }


def build_sibling_frontmatter(
    meta: dict[str, Any],
    kind: str,
    topic: str,
    primary_tag: str,
    parent_alias: str,
    canonical_alias: str,
) -> dict[str, Any]:
    return {
        "date": meta["date"],
        "owner": meta["owner"],
        "researcher": meta["owner"],
        "git_commit": meta["git_commit"],
        "branch": meta["branch"],
        "repository": meta["repository"],
        "topic": topic,
        "tags": [primary_tag, kind],
        "status": "active",
        "last_updated": meta["date"],
        "last_updated_by": meta["owner"],
        "last_updated_note": "Initial bundle scaffolded by ticketsmith.",
        "aliases": [canonical_alias],
        "kind": kind,
        "schema_version": 1,
        "parent": f"[[{parent_alias}]]",
        "depends_on": [],
    }


def ticket_body(topic: str) -> str:
    return (
        f"_Ticket: {topic}. The deliverable is authored in the ticket-write "
        "phase; until then this body is intentionally empty. Process journal: "
        "sibling worklog. Raw Q\u2194R: questions. Findings: research._\n"
    )


def research_body(topic: str) -> str:
    return (
        "# Research\n\n"
        f"**Topic**: {topic}\n\n"
        "_Raw research findings, codebase observations, external references, and "
        "competitor patterns are captured here during the Q\u2194R loop. Updates inline "
        "as subagents return results. Each finding is fact-grade \u2014 no opinions, no "
        "recommendations \u2014 those belong in the ticket itself._\n\n"
        "## Findings\n\n"
        "_(populated during Q\u2194R)_\n"
    )


def questions_body(topic: str) -> str:
    return (
        "# Questions\n\n"
        f"**Topic**: {topic}\n\n"
        "_Running log of grilling exchanges. Each entry records the question asked, "
        "the answer the user gave (or the answer research produced), and brief notes "
        "on alternatives rejected. Only the rare exchange that meets the three-condition "
        "gate (hard-to-reverse + surprising + real trade-off) becomes a Decision Record._\n\n"
        "## Exchanges\n\n"
        "_(populated during Q\u2194R)_\n"
    )


def worklog_body(topic: str) -> str:
    return (
        "# Worklog\n\n"
        f"**Topic**: {topic}\n\n"
        "_QRDSPIV process journal for this bundle. Phase-gate summaries "
        "(Orient \u2192 Readiness \u2192 Design \u2192 Structure \u2192 Plan \u2192 Verify) accumulate "
        "here as the workflow progresses \u2014 the continuity surface a fresh session "
        "reads to resume. The ticket holds only the deliverable; raw Q\u2194R dialogue "
        "lives in the questions file; fact-grade findings in research._\n"
    )


def main() -> int:
    args = parse_args()
    validate_slug(args.slug)

    meta = run_thoughts_metadata()
    short = short_date(meta["date"])
    shared_folder = Path(meta["shared_folder"]).expanduser()
    if not shared_folder.is_absolute():
        # `thoughts metadata` returns a path relative to the repo root; resolve from CWD.
        shared_folder = Path.cwd() / shared_folder

    bundle_dir = shared_folder / "tickets" / args.slug
    if bundle_dir.exists():
        die(
            f"Bundle directory {bundle_dir} already exists. Choose a different slug, or "
            f"resume work on the existing bundle.",
        )

    canonical_ticket = f"ticket-{short}-{args.slug}"
    canonical_research = f"research-{short}-{args.slug}"
    canonical_questions = f"questions-{short}-{args.slug}"
    canonical_worklog = f"worklog-{short}-{args.slug}"

    ticket_fm = build_ticket_frontmatter(
        meta,
        topic=args.topic,
        slug=args.slug,
        primary_tag=args.primary_tag,
        research_alias=canonical_research,
        questions_alias=canonical_questions,
        worklog_alias=canonical_worklog,
        canonical_alias=canonical_ticket,
    )
    research_fm = build_sibling_frontmatter(
        meta,
        kind="research",
        topic=args.topic,
        primary_tag=args.primary_tag,
        parent_alias=canonical_ticket,
        canonical_alias=canonical_research,
    )
    questions_fm = build_sibling_frontmatter(
        meta,
        kind="questions",
        topic=args.topic,
        primary_tag=args.primary_tag,
        parent_alias=canonical_ticket,
        canonical_alias=canonical_questions,
    )
    worklog_fm = build_sibling_frontmatter(
        meta,
        kind="worklog",
        topic=args.topic,
        primary_tag=args.primary_tag,
        parent_alias=canonical_ticket,
        canonical_alias=canonical_worklog,
    )

    bundle_dir.mkdir(parents=True, exist_ok=False)
    ticket_path = bundle_dir / f"{canonical_ticket}.md"
    research_path = bundle_dir / f"{canonical_research}.md"
    questions_path = bundle_dir / f"{canonical_questions}.md"
    worklog_path = bundle_dir / f"{canonical_worklog}.md"

    ticket_path.write_text(emit_frontmatter(ticket_fm) + "\n" + ticket_body(args.topic))
    research_path.write_text(emit_frontmatter(research_fm) + "\n" + research_body(args.topic))
    questions_path.write_text(emit_frontmatter(questions_fm) + "\n" + questions_body(args.topic))
    worklog_path.write_text(emit_frontmatter(worklog_fm) + "\n" + worklog_body(args.topic))

    print(
        json.dumps(
            {
                "bundle_dir": str(bundle_dir),
                "ticket": str(ticket_path),
                "research": str(research_path),
                "questions": str(questions_path),
                "worklog": str(worklog_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
