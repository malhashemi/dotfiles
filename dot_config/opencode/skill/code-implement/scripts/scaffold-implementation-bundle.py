# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
scaffold-implementation-bundle.py — Scaffold an implementation bundle directory.

Creates `{shared_folder}/implementations/YYYY-MM-DD-{ticket-slug}/` containing
one placeholder file at scaffold time:

  - design-YYYY-MM-DD-{ticket-slug}.md   (kind: design, status: draft)

The design placeholder is the only file created at scaffold because design is
the next mandatory artifact after orient (per implementation-workflow-spec
Lock 6: D-phase is always-interactive, always-produced). Other phase artifacts
(structure, plan, plan-N, verification, research) are created by their own
phase skills when those phases execute. This avoids stale empty files.

Date is encoded into BOTH the directory name AND each file name so the
same-ticket-implemented-twice case (revert + redo) creates separate bundles
without collision. The directory date is the scaffold date; subsequent
artifact dates inherit from the directory.

Frontmatter is populated from `thoughts metadata` (date, owner, git_commit,
branch, repository, shared_folder) plus the caller's domain args (ticket-slug,
ticket-alias).

This script is invoked by the code-orient skill once the ticket is loaded and
the workflow has detected planning-mode (vs execution-mode resuming an
existing bundle per Lock 20).

Usage:
    uv run scaffold-implementation-bundle.py \\
        --ticket-slug <kebab-slug> \\
        --ticket-alias <canonical-ticket-alias>

Arguments:
    --ticket-slug    kebab-case slug of the parent ticket (e.g.,
                     `team-workspaces`). Becomes part of the bundle directory
                     name and each artifact filename.
    --ticket-alias   Canonical alias of the parent ticket (e.g.,
                     `ticket-2026-05-17-team-workspaces`). Wrapped in
                     `[[...]]` for the design doc's `parent` frontmatter
                     field.

Exit codes:
    0  Success
    1  Validation error (bad args, invalid slug, bundle collision)
    2  Environment error (thoughts CLI not on PATH, metadata parse failed)

Output (stdout): JSON object with the bundle directory and design placeholder
paths, suitable for the calling skill to capture and pass downstream:
    {
      "bundle_dir": "/.../implementations/2026-05-17-team-workspaces",
      "design": "/.../implementations/2026-05-17-team-workspaces/design-2026-05-17-team-workspaces.md",
      "ticket_slug": "team-workspaces",
      "ticket_alias": "ticket-2026-05-17-team-workspaces",
      "design_canonical_alias": "design-2026-05-17-team-workspaces"
    }
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")
ALIAS_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")


def die(msg: str, code: int = 1) -> None:
    """Print an error to stderr and exit."""
    print(f"scaffold-implementation-bundle: {msg}", file=sys.stderr)
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
            "`thoughts` CLI not found on PATH. Install thoughts-cli or run "
            "`thoughts init` in the current repository.",
            code=2,
        )
    except subprocess.CalledProcessError as exc:
        die(
            f"`thoughts metadata` failed (exit {exc.returncode}). "
            f"Stderr: {exc.stderr.strip()}",
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

    required = (
        "date",
        "owner",
        "git_commit",
        "branch",
        "repository",
        "shared_folder",
    )
    missing = [k for k in required if k not in meta]
    if missing:
        die(
            f"`thoughts metadata` output is missing required keys: "
            f"{', '.join(missing)}. Run `thoughts metadata` manually to inspect.",
            code=2,
        )
    return meta


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scaffold an implementation bundle directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ticket-slug",
        required=True,
        help="kebab-case slug of the parent ticket.",
    )
    parser.add_argument(
        "--ticket-alias",
        required=True,
        help=(
            "Canonical alias of the parent ticket (e.g., "
            "ticket-2026-05-17-team-workspaces). Wrapped in [[...]] in "
            "the design doc's `parent` field."
        ),
    )
    return parser.parse_args()


def validate_slug(slug: str) -> None:
    if not SLUG_RE.match(slug):
        die(
            f"Ticket slug {slug!r} is invalid. Use lowercase letters, digits, "
            "and single hyphens; start and end with an alphanumeric character "
            "(e.g., `team-workspaces`)."
        )


def validate_alias(alias: str) -> None:
    if not ALIAS_RE.match(alias):
        die(
            f"Ticket alias {alias!r} is invalid. Aliases use the same rules "
            "as slugs (lowercase, digits, single hyphens, start/end "
            "alphanumeric)."
        )


def short_date(iso_or_date: str) -> str:
    """Extract YYYY-MM-DD from an ISO 8601 timestamp or pass through a date."""
    if len(iso_or_date) >= 10 and iso_or_date[4] == "-" and iso_or_date[7] == "-":
        return iso_or_date[:10]
    die(
        f"Cannot extract date from {iso_or_date!r} (expected ISO 8601 prefix).",
        code=2,
    )
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


def build_design_frontmatter(
    meta: dict[str, Any],
    ticket_slug: str,
    ticket_alias: str,
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
        "topic": f"Design for {ticket_slug}",
        "tags": ["design"],
        "status": "draft",
        "last_updated": meta["date"],
        "last_updated_by": meta["owner"],
        "last_updated_note": "Initial design placeholder scaffolded by codesmith.",
        "aliases": [canonical_alias],
        "kind": "design",
        "schema_version": 1,
        "parent": f"[[{ticket_alias}]]",
        "depends_on": [],
    }


def design_body(ticket_slug: str, ticket_alias: str) -> str:
    return (
        "# Design\n\n"
        f"**Parent ticket**: [[{ticket_alias}]]\n\n"
        "**Status**: draft (D-phase in progress)\n\n"
        "_This design document is the highest-leverage artifact in the "
        "implementation workflow. It converts codebase reality (from R-phase) "
        "into a designed solution. The agent presents; the human brain-surgeries "
        "via Question tool per substantive decision; iterate until aligned. The "
        "three sections below are filled during D-phase by the `code-design` skill._\n\n"
        "## Current state\n\n"
        "_(populated during D-phase: grounding from R findings; what the touched "
        "area currently looks like; what patterns/types/invariants exist)_\n\n"
        "## Desired end state\n\n"
        "_(populated during D-phase: what the solved problem looks like in the "
        "codebase after implementation; behavioral end-state per AC; structural "
        "end-state per design choices)_\n\n"
        "## Design decisions\n\n"
        "_(populated during D-phase: architectural choices made with brief "
        "rationale; type/interface decisions; vertical-slice identification; "
        "risk areas; if D identifies multiple plans, list them here with "
        "one-line scopes)_\n"
    )


def main() -> int:
    args = parse_args()
    validate_slug(args.ticket_slug)
    validate_alias(args.ticket_alias)

    meta = run_thoughts_metadata()
    short = short_date(meta["date"])
    shared_folder = Path(meta["shared_folder"]).expanduser()
    if not shared_folder.is_absolute():
        # `thoughts metadata` returns a path relative to the repo root; resolve from CWD.
        shared_folder = Path.cwd() / shared_folder

    bundle_dir_name = f"{short}-{args.ticket_slug}"
    bundle_dir = shared_folder / "implementations" / bundle_dir_name
    if bundle_dir.exists():
        die(
            f"Bundle directory {bundle_dir} already exists. The same ticket "
            "implemented on the same date would collide. If this is a "
            "re-implementation, wait until tomorrow or remove the existing "
            "bundle. If this is a resumption, re-invoke the codesmith workflow "
            "in execution mode with the existing bundle path.",
        )

    canonical_design = f"design-{short}-{args.ticket_slug}"

    design_fm = build_design_frontmatter(
        meta,
        ticket_slug=args.ticket_slug,
        ticket_alias=args.ticket_alias,
        canonical_alias=canonical_design,
    )

    bundle_dir.mkdir(parents=True, exist_ok=False)
    design_path = bundle_dir / f"{canonical_design}.md"
    design_path.write_text(
        emit_frontmatter(design_fm)
        + "\n"
        + design_body(args.ticket_slug, args.ticket_alias)
    )

    print(
        json.dumps(
            {
                "bundle_dir": str(bundle_dir),
                "design": str(design_path),
                "ticket_slug": args.ticket_slug,
                "ticket_alias": args.ticket_alias,
                "design_canonical_alias": canonical_design,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
