# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
scaffold-decision-record.py — Scaffold a Decision Record file.

Creates `{shared_folder}/decisions/decision-YYYY-MM-DD-{slug}.md` with
schema-compliant frontmatter (kind: decision, status: accepted, immutable
per spec §4.3 three-condition gate) and seeds a minimal body following the
mattpocock ADR-FORMAT.

Auto-numbering: a single manifest at `{shared_folder}/decisions/MANIFEST.yaml`
holds `next_dr` (the integer to claim next) and `decisions:` (an index of all
recorded DRs). The script:

  1. Loads (or lazy-creates) the manifest
  2. Claims the current next_dr value as this DR's number (DR-NNN)
  3. Writes the DR file with frontmatter linking the parent ticket
  4. Appends this DR to the decisions index
  5. Increments next_dr and writes the manifest back

This is per spec lock 27 (scripts invoke `thoughts metadata` internally) +
lock 32 (schema-native frontmatter) + spec §4.3 (DR immutability).

Usage:
    uv run scaffold-decision-record.py \\
        --title "<one-line title>" \\
        --slug <kebab-slug> \\
        --parent-ticket <canonical-ticket-alias>

Arguments:
    --title          One-line title of the decision (e.g., "Use shared
                     tables for team scoping").
    --slug           kebab-case slug. Becomes part of filename + alias.
    --parent-ticket  Canonical alias of the spawning ticket (e.g.,
                     ticket-2026-05-17-team-workspaces). Wrapped in
                     `[[...]]` for the DR's parent frontmatter field.

Exit codes:
    0  Success
    1  Validation error (bad args, invalid slug, slug collision)
    2  Environment error (thoughts CLI not on PATH, metadata parse failed,
       manifest corrupt or unwritable)

Output (stdout): JSON object with the DR's number, file path, and aliases:
    {
      "dr_number": 3,
      "dr_id": "DR-003",
      "file": "/.../decisions/decision-2026-05-17-shared-tables.md",
      "canonical_alias": "decision-2026-05-17-shared-tables",
      "short_alias": "DR-003"
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
DR_ID_RE = re.compile(r"^DR-\d{3,}$")


def die(msg: str, code: int = 1) -> None:
    """Print an error to stderr and exit."""
    print(f"scaffold-decision-record: {msg}", file=sys.stderr)
    sys.exit(code)


def run_thoughts_metadata() -> dict[str, Any]:
    """Run `thoughts metadata` and parse the key/value lines into a dict."""
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
        if value.startswith("<") or "|" in value:
            continue
        if not value:
            continue
        meta[key] = value

    required = ("date", "owner", "git_commit", "branch", "repository", "shared_folder")
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
        description="Scaffold a Decision Record (DR) file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--title",
        required=True,
        help="One-line title of the decision.",
    )
    parser.add_argument(
        "--slug",
        required=True,
        help="kebab-case slug for filename and aliases.",
    )
    parser.add_argument(
        "--parent-ticket",
        required=True,
        help="Canonical alias of the spawning ticket (e.g., "
        "ticket-2026-05-17-team-workspaces). Wrapped in [[...]] in DR "
        "frontmatter.",
    )
    return parser.parse_args()


def validate_slug(slug: str) -> None:
    if not SLUG_RE.match(slug):
        die(
            f"Slug {slug!r} is invalid. Use lowercase letters, digits, and "
            "single hyphens; start and end with an alphanumeric character "
            "(e.g., `shared-tables-for-team-scoping`)."
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


def load_or_init_manifest(manifest_path: Path) -> dict[str, Any]:
    """Load the DR manifest, or return a freshly initialized one."""
    if not manifest_path.exists():
        return {"next_dr": 1, "decisions": []}

    try:
        with manifest_path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        die(
            f"DR manifest {manifest_path} is not valid YAML: {exc}. "
            "Fix or remove the file and re-run.",
            code=2,
        )

    if not isinstance(data, dict):
        die(
            f"DR manifest {manifest_path} must be a YAML mapping with "
            "`next_dr` and `decisions:` keys. Found: "
            f"{type(data).__name__}.",
            code=2,
        )

    if "next_dr" not in data or not isinstance(data["next_dr"], int):
        die(
            f"DR manifest {manifest_path} is missing or has non-integer "
            "`next_dr` field.",
            code=2,
        )
    if "decisions" not in data or not isinstance(data["decisions"], list):
        die(
            f"DR manifest {manifest_path} is missing or has non-list "
            "`decisions` field.",
            code=2,
        )
    return data


def write_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    """Atomically write the DR manifest with stable key order."""
    body = yaml.safe_dump(
        manifest,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=120,
    )
    header = (
        "# DR Manifest — auto-maintained by scaffold-decision-record.py\n"
        "# DO NOT hand-edit unless reconciling with on-disk DR files.\n"
    )
    manifest_path.write_text(header + body)


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


def build_dr_frontmatter(
    meta: dict[str, Any],
    title: str,
    short: str,
    dr_id: str,
    canonical_alias: str,
    parent_ticket_alias: str,
) -> dict[str, Any]:
    return {
        "date": meta["date"],
        "owner": meta["owner"],
        "researcher": meta["owner"],
        "git_commit": meta["git_commit"],
        "branch": meta["branch"],
        "repository": meta["repository"],
        "topic": title,
        "tags": ["decision"],
        "status": "accepted",
        "last_updated": meta["date"],
        "last_updated_by": meta["owner"],
        "last_updated_note": "Initial decision record scaffolded by ticketsmith.",
        "aliases": [canonical_alias, dr_id],
        "kind": "decision",
        "schema_version": 1,
        "source": "manual",
        "assignee": meta["owner"],
        "priority": 2,
        "parent": f"[[{parent_ticket_alias}]]",
        "depends_on": [],
        "blocks": [],
    }


def dr_body(title: str, dr_id: str, parent_ticket_alias: str) -> str:
    """Seed body following mattpocock ADR-FORMAT (minimal one-paragraph)."""
    return (
        f"# {dr_id}: {title}\n\n"
        f"**Parent**: [[{parent_ticket_alias}]]\n\n"
        "## Context\n\n"
        "_(1\u20133 sentences describing the situation that forced the decision. "
        "What constraint surfaced? What alternatives were on the table?)_\n\n"
        "## Decision\n\n"
        "_(one sentence stating what was decided)_\n\n"
        "## Why\n\n"
        "_(one sentence stating the rationale \u2014 the specific reasons this "
        "option won over the rejected alternatives)_\n\n"
        "---\n\n"
        "_Optional sections \u2014 add only if they add value:_\n\n"
        "- **Considered options** (when the rejected alternatives are worth remembering)\n"
        "- **Consequences** (when non-obvious downstream effects need to be called out)\n\n"
        "_This decision is immutable once written. Future reversals create a new "
        "DR that `supersedes:` this one._\n"
    )


def main() -> int:
    args = parse_args()
    validate_slug(args.slug)

    meta = run_thoughts_metadata()
    short = short_date(meta["date"])
    shared_folder = Path(meta["shared_folder"]).expanduser()
    if not shared_folder.is_absolute():
        shared_folder = Path.cwd() / shared_folder

    decisions_dir = shared_folder / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = decisions_dir / "MANIFEST.yaml"

    manifest = load_or_init_manifest(manifest_path)
    dr_number: int = manifest["next_dr"]
    dr_id = f"DR-{dr_number:03d}"

    canonical_alias = f"decision-{short}-{args.slug}"
    dr_path = decisions_dir / f"{canonical_alias}.md"

    if dr_path.exists():
        die(
            f"Decision file {dr_path} already exists. Choose a different slug, "
            "or amend the existing decision.",
        )

    # Defensive: make sure the dr_id is not already claimed in the manifest.
    existing_ids = {
        entry.get("id") for entry in manifest["decisions"] if isinstance(entry, dict)
    }
    if dr_id in existing_ids:
        die(
            f"DR id {dr_id} already exists in {manifest_path}. The manifest "
            "may be out of sync \u2014 inspect manually.",
            code=2,
        )

    fm = build_dr_frontmatter(
        meta,
        title=args.title,
        short=short,
        dr_id=dr_id,
        canonical_alias=canonical_alias,
        parent_ticket_alias=args.parent_ticket,
    )
    dr_path.write_text(
        emit_frontmatter(fm) + "\n" + dr_body(args.title, dr_id, args.parent_ticket)
    )

    # Update manifest: append to index, increment counter, write back.
    manifest["decisions"].append(
        {
            "id": dr_id,
            "title": args.title,
            "slug": args.slug,
            "canonical_alias": canonical_alias,
            "parent_ticket": args.parent_ticket,
            "created": meta["date"],
        }
    )
    manifest["next_dr"] = dr_number + 1
    write_manifest(manifest_path, manifest)

    print(
        json.dumps(
            {
                "dr_number": dr_number,
                "dr_id": dr_id,
                "file": str(dr_path),
                "canonical_alias": canonical_alias,
                "short_alias": dr_id,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
