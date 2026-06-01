# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
stamp-frontmatter.py — Update last_updated metadata on a thoughts artifact.

Refreshes three frontmatter fields on a single file:
  - last_updated       (set to current ISO 8601 timestamp from `thoughts metadata`)
  - last_updated_by    (set to current owner)
  - last_updated_note  (REPLACED with the --note value; old note preserved
                        only in git history)

The body of the file is preserved verbatim. The frontmatter is re-emitted
with stable key order. Datetime fields (`date`, `last_updated`) are normalized
to canonical ISO-8601 with a `T` separator, so this script — the last writer in
the stamp/transition flow — always emits schema-valid output even if an upstream
writer (e.g. the external `thoughts backlog mark` CLI) left them space-separated.

This is called by ticketsmith skills after every bundle file edit
(ticket, research, questions, decision) so the audit trail reflects who
touched the file last and what changed.

Usage:
    uv run stamp-frontmatter.py --file <path> [--note "<message>"]

Arguments:
    --file   Absolute or CWD-relative path to a .md file with `---`
             frontmatter. Required.
    --note   One-line message describing what just changed. Default:
             \"Updated by ticketsmith.\" — agents SHOULD pass a meaningful
             note; the default exists so calls never fail.

Exit codes:
    0  Success
    1  Validation error (file missing, no frontmatter, malformed YAML)
    2  Environment error (thoughts CLI not on PATH, metadata parse failed)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

FRONTMATTER_RE = re.compile(
    r"\A---\r?\n(?P<fm>.*?)\r?\n---\r?\n(?P<body>.*)\Z",
    re.DOTALL,
)

# Frontmatter datetime fields must round-trip as canonical ISO-8601 with a `T`
# separator. Upstream writers can re-emit them space-separated/unquoted, and
# PyYAML then loads such scalars as datetime objects. This script is the LAST
# writer in the stamp/transition flow, so it normalizes them defensively.
_DATETIME_KEYS = ("date", "last_updated")


def canonicalize_iso(value: Any) -> Any:
    """Coerce a date/datetime object or space-separated string to ISO-8601
    with a `T` separator. Non-datetime values pass through untouched."""
    if isinstance(value, date):  # also matches datetime (a date subclass)
        return value.isoformat()
    if isinstance(value, str):
        m = re.match(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}.*)$", value)
        if m:
            return f"{m.group(1)}T{m.group(2)}"
    return value


def die(msg: str, code: int = 1) -> None:
    """Print an error to stderr and exit."""
    print(f"stamp-frontmatter: {msg}", file=sys.stderr)
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

    required = ("date", "owner")
    missing = [k for k in required if k not in meta]
    if missing:
        die(
            f"`thoughts metadata` output is missing required keys: "
            f"{', '.join(missing)}.",
            code=2,
        )
    return meta


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update last_updated metadata on a thoughts artifact.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the .md file whose frontmatter should be stamped.",
    )
    parser.add_argument(
        "--note",
        default="Updated by ticketsmith.",
        help='One-line note describing the update. Default: "Updated by ticketsmith."',
    )
    return parser.parse_args()


def split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Split a file's content into (frontmatter dict, body string).

    The frontmatter must be the first block: opens with `---\\n`, closes
    with `\\n---\\n`. Body is everything after.
    """
    match = FRONTMATTER_RE.match(content)
    if not match:
        die(
            "File does not start with a YAML frontmatter block. Expected the "
            "file to begin with `---` on its own line, followed by YAML, then "
            "`---` on its own line.",
        )
        return {}, ""  # unreachable; satisfies type checker

    fm_text = match.group("fm")
    body = match.group("body")

    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        die(f"Frontmatter YAML is malformed: {exc}")
        return {}, ""  # unreachable

    if not isinstance(fm, dict):
        die(
            f"Frontmatter must be a YAML mapping; found {type(fm).__name__}.",
        )
        return {}, ""  # unreachable

    return fm, body


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


def main() -> int:
    args = parse_args()

    file_path = Path(args.file).expanduser().resolve()
    if not file_path.exists():
        die(f"File {file_path} does not exist.")
    if not file_path.is_file():
        die(f"{file_path} is not a regular file.")

    meta = run_thoughts_metadata()
    content = file_path.read_text()
    fm, body = split_frontmatter(content)

    fm["last_updated"] = meta["date"]
    fm["last_updated_by"] = meta["owner"]
    fm["last_updated_note"] = args.note

    for key in _DATETIME_KEYS:
        if key in fm:
            fm[key] = canonicalize_iso(fm[key])

    file_path.write_text(emit_frontmatter(fm) + body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
