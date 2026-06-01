# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
transition-ticket-status.py — Transition an implementation ticket's status.

Wraps the `thoughts backlog mark` CLI with status-transition validation
appropriate for the implementation workflow, then stamps last_updated
metadata via stamp-frontmatter.py.

Workflow transitions (per implementation-workflow-spec §2 + ticketsmith
Lock 32):

  ready → active → implemented → verified

Each transition has a specific point in the workflow:

  - ready → active        : code-orient (entering planning session)
  - active → implemented  : code-verify (all gates PROCEED, code merged)
  - implemented → verified: optional post-merge verification (e.g., push-CI
                            on target branch passes; typically same session)

This script does NOT enforce strict ordering (the workflow does). It DOES
reject statuses outside the implementation workflow's lifecycle (draft,
blocked, abandoned, archived) — those transitions belong to ticketsmith
or backlog hygiene, not codesmith.

Per spec Lock 24 + spec session verification: `thoughts backlog mark <id>
ready` works at the CLI level despite the help output omitting `ready`
from the valid status list. This script can therefore safely target any
of the four workflow statuses.

Usage:
    uv run transition-ticket-status.py \\
        --ticket-file <path> \\
        --new-status <ready|active|implemented|verified>

Arguments:
    --ticket-file   Absolute or CWD-relative path to the ticket .md file.
                    Frontmatter must include `aliases:` so the canonical
                    alias can be extracted for the CLI call.
    --new-status    Target status. Must be one of: ready, active,
                    implemented, verified.

Exit codes:
    0  Success
    1  Validation error (bad args, invalid status, missing ticket file,
       no aliases in frontmatter)
    2  Environment error (thoughts CLI not on PATH, `thoughts backlog mark`
       failed, stamp-frontmatter.py failed)

Output (stdout): JSON object confirming the transition:
    {
      "ticket_file": "/.../tickets/team-workspaces/ticket-...md",
      "canonical_alias": "ticket-2026-05-17-team-workspaces",
      "old_status": "ready",
      "new_status": "active",
      "stamped": true
    }

Side effects:
  - Updates the ticket's `status:` frontmatter via `thoughts backlog mark`
  - Updates last_updated/last_updated_by/last_updated_note via
    stamp-frontmatter.py with a workflow-specific note
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

VALID_TRANSITIONS = {"ready", "active", "implemented", "verified"}

FRONTMATTER_RE = re.compile(
    r"\A---\r?\n(?P<fm>.*?)\r?\n---\r?\n(?P<body>.*)\Z",
    re.DOTALL,
)

# Human-readable notes that describe the workflow-relevant meaning of each
# transition. These get stamped onto last_updated_note so the audit trail
# reflects which workflow stage triggered the change.
TRANSITION_NOTES = {
    "ready": (
        "Marked ready by codesmith after V-phase passed during ticket-writing. "
        "Available for implementation pickup."
    ),
    "active": (
        "Picked up by codesmith for implementation. Entering planning session."
    ),
    "implemented": (
        "Codesmith I-phase complete; code merged. Awaiting final verification."
    ),
    "verified": (
        "Codesmith V-phase complete; final-integration gate passed; "
        "post-merge checks (if applicable) clean."
    ),
}


def die(msg: str, code: int = 1) -> None:
    """Print an error to stderr and exit."""
    print(f"transition-ticket-status: {msg}", file=sys.stderr)
    sys.exit(code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transition an implementation ticket's workflow status.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--ticket-file",
        required=True,
        help="Path to the ticket .md file.",
    )
    parser.add_argument(
        "--new-status",
        required=True,
        choices=sorted(VALID_TRANSITIONS),
        help="Target status (one of: ready, active, implemented, verified).",
    )
    return parser.parse_args()


def split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Split a file's content into (frontmatter dict, body string)."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        die(
            "Ticket file does not start with a YAML frontmatter block. "
            "Expected the file to begin with `---` on its own line, followed "
            "by YAML, then `---` on its own line."
        )
        return {}, ""  # unreachable

    fm_text = match.group("fm")
    body = match.group("body")

    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        die(f"Frontmatter YAML is malformed: {exc}")
        return {}, ""  # unreachable

    if not isinstance(fm, dict):
        die(
            f"Frontmatter must be a YAML mapping; found {type(fm).__name__}."
        )
        return {}, ""  # unreachable

    return fm, body


def extract_canonical_alias(fm: dict[str, Any], ticket_path: Path) -> str:
    """Extract the canonical alias from the ticket frontmatter.

    Convention (per ticketsmith Lock 32): the first entry in `aliases:` is
    the canonical alias (e.g., `ticket-2026-05-17-team-workspaces`). This
    is the ID that `thoughts backlog mark` expects.
    """
    aliases = fm.get("aliases")
    if not aliases or not isinstance(aliases, list) or not aliases:
        die(
            f"Ticket {ticket_path} frontmatter has no `aliases:` list, or "
            "the list is empty. The canonical alias is required to call "
            "`thoughts backlog mark`."
        )
    canonical = aliases[0]
    if not isinstance(canonical, str) or not canonical:
        die(
            f"Ticket {ticket_path} frontmatter `aliases[0]` is not a "
            "non-empty string."
        )
    return canonical


def extract_current_status(fm: dict[str, Any], ticket_path: Path) -> str:
    """Extract the current status from the ticket frontmatter."""
    status = fm.get("status")
    if not isinstance(status, str) or not status:
        die(
            f"Ticket {ticket_path} frontmatter has no `status:` string. "
            "Cannot determine the current status to transition from."
        )
    return status


def call_thoughts_backlog_mark(canonical: str, new_status: str) -> None:
    """Invoke `thoughts backlog mark <id> <status>` and surface errors."""
    try:
        subprocess.run(
            ["thoughts", "backlog", "mark", canonical, new_status],
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
            f"`thoughts backlog mark {canonical} {new_status}` failed (exit "
            f"{exc.returncode}). Stderr: {exc.stderr.strip()}",
            code=2,
        )


def call_stamp_frontmatter(ticket_path: Path, note: str) -> None:
    """Invoke the sibling stamp-frontmatter.py script.

    Resolves the sibling script relative to THIS file's directory so the
    script works regardless of CWD or how the calling skill addresses it.
    """
    stamp_script = Path(__file__).parent / "stamp-frontmatter.py"
    if not stamp_script.exists():
        die(
            f"Sibling script {stamp_script} does not exist. "
            "transition-ticket-status.py expects stamp-frontmatter.py to "
            "live in the same directory.",
            code=2,
        )
    try:
        subprocess.run(
            [
                "uv",
                "run",
                str(stamp_script),
                "--file",
                str(ticket_path),
                "--note",
                note,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        die(
            "`uv` not found on PATH. Install uv or invoke stamp-frontmatter "
            "manually after this script.",
            code=2,
        )
    except subprocess.CalledProcessError as exc:
        die(
            f"stamp-frontmatter.py failed (exit {exc.returncode}). "
            f"Stderr: {exc.stderr.strip()}",
            code=2,
        )


def main() -> int:
    args = parse_args()

    ticket_path = Path(args.ticket_file).expanduser().resolve()
    if not ticket_path.exists():
        die(f"Ticket file {ticket_path} does not exist.")
    if not ticket_path.is_file():
        die(f"{ticket_path} is not a regular file.")

    content = ticket_path.read_text()
    fm, _body = split_frontmatter(content)

    canonical = extract_canonical_alias(fm, ticket_path)
    old_status = extract_current_status(fm, ticket_path)

    if old_status == args.new_status:
        die(
            f"Ticket {canonical} is already at status {args.new_status!r}; "
            "nothing to do. If this is unexpected, inspect the ticket "
            "frontmatter manually."
        )

    note = TRANSITION_NOTES[args.new_status]

    call_thoughts_backlog_mark(canonical, args.new_status)
    call_stamp_frontmatter(ticket_path, note)

    print(
        json.dumps(
            {
                "ticket_file": str(ticket_path),
                "canonical_alias": canonical,
                "old_status": old_status,
                "new_status": args.new_status,
                "stamped": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
