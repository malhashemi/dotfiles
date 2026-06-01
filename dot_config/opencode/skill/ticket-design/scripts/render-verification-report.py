# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
render-verification-report.py — Render JSON findings into the verification doc.

Takes structured JSON findings produced by the codesmith-validator subagent
and renders them as a per-gate entry in the bundle's verification doc:

  {bundle_dir}/verification-YYYY-MM-DD-{ticket-slug}.md

The verification doc is a SINGLE artifact per implementation bundle that
accumulates gate-by-gate entries across the workflow's five V-phase gates
(per implementation-workflow-spec Lock 11.5):

  1. D-review            (after D, before S)
  2. P-review            (after P, before Work-Tree)
  3. I-per-slice         (after each I-phase slice)
  4. final-integration   (after all slices verified)
  5. PR-review           (after PR opened; conditional on PR mode)

Each render appends a new section to the doc (creating the doc with
frontmatter on first call). The doc is considered finalized at V-completion
(after final-integration or PR-review). Discipline-based, not
filesystem-enforced — the script does not refuse to append to a "done" doc.

Verdict model (per Lock 11.4): BINARY (PROCEED | BLOCKED). There is NO
PROCEED_WITH_NOTES. Severity-driven blocking:
  - Any Critical or High finding   → auto-BLOCKED
  - Any Medium finding             → BLOCKED unless explicitly waived by user
  - Only Low / Suggestion          → PROCEED

Severity ladder (per Lock 11.4, 5-tier — distinct from ticket-verify's
4-tier ladder): Critical / High / Medium / Low / Suggestion.

Mechanism-per-angle (per Lock 11.3): each angle is either a fitness function
(deterministic, runs first, blocking) or LLM (judgment-driven, runs only on
what fitness functions passed).

Loop-back routing (per Lock 11.6): when BLOCKED, the validator's report
identifies which phase needs the fix. The script renders this routing
verbatim into the doc so the orchestrator (code-verify skill) can act on it.

Usage:
    uv run render-verification-report.py \\
        --findings <findings.json> \\
        --bundle-dir <path> \\
        --ticket-slug <slug> \\
        --ticket-alias <canonical-alias> \\
        [--stdout-only]

Arguments:
    --findings        Path to a JSON file containing the validator's
                      structured findings. See schema below.
    --bundle-dir      Path to the implementation bundle directory. The
                      verification doc is created/appended at
                      {bundle_dir}/verification-{YYYY-MM-DD}-{slug}.md.
    --ticket-slug     kebab-case slug of the parent ticket. Used in the
                      verification doc filename.
    --ticket-alias    Canonical alias of the parent ticket (e.g.,
                      ticket-2026-05-17-team-workspaces). Wrapped in
                      [[...]] in the verification doc's `parent` field.
    --stdout-only     If set, render to stdout only; do NOT create or
                      modify the verification doc. Useful for previewing.

Exit codes:
    0  Success
    1  Validation error (bad args, malformed JSON, schema violation)
    2  Environment error (thoughts CLI not on PATH, metadata parse failed,
       I/O failure)

JSON findings schema (top-level keys; validation enforces presence):

    {
      "gate": "D-review" | "P-review" | "I-per-slice" | "final-integration" | "PR-review",
      "slice_id": "1.2",        // ONLY for I-per-slice gate; omit otherwise
      "verdict": "PROCEED" | "BLOCKED",
      "summary": "1-2 sentence assessment",
      "loop_back_target": "I-phase" | "P-phase" | "S-phase" | "D-phase" | null,
      "angles": [
        {
          "name": "plan-adherence" | "code-quality" | ... ,
          "mechanism": "fitness-function" | "llm",
          "result": "pass" | "fail" | "n/a",
          "detail": "...",      // human-readable result narrative
          "findings": [
            {
              "id": "C-1",
              "severity": "Critical" | "High" | "Medium" | "Low" | "Suggestion",
              "title": "...",
              "location": "src/foo.ts:42",
              "finding": "2-3 sentences",
              "fix": "concrete action",
              "impact": "if not fixed",                  // Medium+ ONLY
              "scope": "this-impl" | "codebase-wide",    // optional; default this-impl
              "user_waived": false                       // optional; default false
            }
          ]
        }
      ],
      "next_steps": ["..."]
    }

Output (stdout): JSON object confirming the render:
    {
      "verification_doc": "/.../verification-2026-05-17-team-workspaces.md",
      "gate": "P-review",
      "verdict": "BLOCKED",
      "loop_back_target": "P-phase",
      "appended": true
    }
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

VALID_GATES = {
    "D-review",
    "P-review",
    "I-per-slice",
    "final-integration",
    "PR-review",
}
VALID_VERDICTS = {"PROCEED", "BLOCKED"}
VALID_LOOP_BACK_TARGETS = {"I-phase", "P-phase", "S-phase", "D-phase"}
VALID_SEVERITIES = ("Critical", "High", "Medium", "Low", "Suggestion")
VALID_MECHANISMS = {"fitness-function", "llm"}
VALID_RESULTS = {"pass", "fail", "n/a"}
VALID_SCOPES = {"this-impl", "codebase-wide"}
SEVERITY_INITIALS = {
    "Critical": "C",
    "High": "H",
    "Medium": "M",
    "Low": "L",
    "Suggestion": "S",
}

FRONTMATTER_RE = re.compile(
    r"\A---\r?\n(?P<fm>.*?)\r?\n---\r?\n(?P<body>.*)\Z",
    re.DOTALL,
)


def die(msg: str, code: int = 1) -> None:
    """Print an error to stderr and exit."""
    print(f"render-verification-report: {msg}", file=sys.stderr)
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

    required = ("date", "owner", "git_commit", "branch", "repository")
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
        description="Render JSON findings into the verification doc.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--findings",
        required=True,
        help="Path to a JSON file containing the validator's findings.",
    )
    parser.add_argument(
        "--bundle-dir",
        required=True,
        help="Path to the implementation bundle directory.",
    )
    parser.add_argument(
        "--ticket-slug",
        required=True,
        help="kebab-case slug of the parent ticket.",
    )
    parser.add_argument(
        "--ticket-alias",
        required=True,
        help="Canonical alias of the parent ticket.",
    )
    parser.add_argument(
        "--stdout-only",
        action="store_true",
        help="Render to stdout only; do not modify the verification doc.",
    )
    return parser.parse_args()


def short_date(iso_or_date: str) -> str:
    """Extract YYYY-MM-DD from an ISO 8601 timestamp or pass through a date."""
    if len(iso_or_date) >= 10 and iso_or_date[4] == "-" and iso_or_date[7] == "-":
        return iso_or_date[:10]
    die(
        f"Cannot extract date from {iso_or_date!r} (expected ISO 8601 prefix).",
        code=2,
    )
    return ""  # unreachable


def load_findings(findings_path: Path) -> dict[str, Any]:
    """Load and validate the JSON findings document."""
    if not findings_path.exists():
        die(f"Findings file {findings_path} does not exist.")
    try:
        with findings_path.open() as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        die(f"Findings file {findings_path} is not valid JSON: {exc}")
        return {}  # unreachable

    if not isinstance(data, dict):
        die(
            f"Findings file {findings_path} must contain a JSON object at "
            f"the top level; found {type(data).__name__}."
        )

    # Required top-level keys
    for key in ("gate", "verdict", "summary", "angles"):
        if key not in data:
            die(f"Findings missing required top-level key: {key!r}.")

    if data["gate"] not in VALID_GATES:
        die(
            f"Findings `gate` is {data['gate']!r}; must be one of: "
            f"{sorted(VALID_GATES)}."
        )

    if data["verdict"] not in VALID_VERDICTS:
        die(
            f"Findings `verdict` is {data['verdict']!r}; must be one of: "
            f"{sorted(VALID_VERDICTS)} (binary per Lock 11.4 — there is no "
            "PROCEED_WITH_NOTES)."
        )

    if data["gate"] == "I-per-slice" and not data.get("slice_id"):
        die(
            "Findings for the I-per-slice gate must include a `slice_id` "
            "field (e.g., '1.2')."
        )

    loop_back = data.get("loop_back_target")
    if loop_back is not None and loop_back not in VALID_LOOP_BACK_TARGETS:
        die(
            f"Findings `loop_back_target` is {loop_back!r}; must be one of: "
            f"{sorted(VALID_LOOP_BACK_TARGETS)} or null."
        )

    if data["verdict"] == "BLOCKED" and loop_back is None:
        die(
            "BLOCKED verdict requires a non-null `loop_back_target` (per "
            "Lock 11.6 loop-back routing)."
        )

    if not isinstance(data["angles"], list):
        die("Findings `angles` must be a list.")

    for i, angle in enumerate(data["angles"]):
        if not isinstance(angle, dict):
            die(f"Findings `angles[{i}]` must be an object.")
        for k in ("name", "mechanism", "result", "findings"):
            if k not in angle:
                die(f"Findings `angles[{i}]` missing required key: {k!r}.")
        if angle["mechanism"] not in VALID_MECHANISMS:
            die(
                f"Findings `angles[{i}].mechanism` is {angle['mechanism']!r}; "
                f"must be one of: {sorted(VALID_MECHANISMS)}."
            )
        if angle["result"] not in VALID_RESULTS:
            die(
                f"Findings `angles[{i}].result` is {angle['result']!r}; "
                f"must be one of: {sorted(VALID_RESULTS)}."
            )
        if not isinstance(angle["findings"], list):
            die(f"Findings `angles[{i}].findings` must be a list.")
        for j, finding in enumerate(angle["findings"]):
            if not isinstance(finding, dict):
                die(f"Findings `angles[{i}].findings[{j}]` must be an object.")
            for k in ("id", "severity", "title", "location", "finding", "fix"):
                if k not in finding:
                    die(
                        f"Findings `angles[{i}].findings[{j}]` missing "
                        f"required key: {k!r}."
                    )
            if finding["severity"] not in VALID_SEVERITIES:
                die(
                    f"Findings `angles[{i}].findings[{j}].severity` is "
                    f"{finding['severity']!r}; must be one of: "
                    f"{list(VALID_SEVERITIES)}."
                )
            if finding["severity"] in ("Critical", "High", "Medium") and "impact" not in finding:
                die(
                    f"Findings `angles[{i}].findings[{j}]` has severity "
                    f"{finding['severity']!r} and requires an `impact` field "
                    "(Medium+ findings must state what happens if not fixed)."
                )
            scope = finding.get("scope", "this-impl")
            if scope not in VALID_SCOPES:
                die(
                    f"Findings `angles[{i}].findings[{j}].scope` is "
                    f"{scope!r}; must be one of: {sorted(VALID_SCOPES)}."
                )

    return data


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


def build_initial_frontmatter(
    meta: dict[str, Any],
    ticket_slug: str,
    ticket_alias: str,
    canonical_alias: str,
) -> dict[str, Any]:
    return {
        "date": meta["date"],
        "owner": meta["owner"],
        "researcher": meta["owner"],
        "git_commit": meta["git_commit"],
        "branch": meta["branch"],
        "repository": meta["repository"],
        "topic": f"Verification for {ticket_slug}",
        "tags": ["verification"],
        "status": "active",
        "last_updated": meta["date"],
        "last_updated_by": meta["owner"],
        "last_updated_note": (
            "Initial verification doc created by codesmith on first gate "
            "with findings."
        ),
        "aliases": [canonical_alias],
        "kind": "verification",
        "schema_version": 1,
        "parent": f"[[{ticket_alias}]]",
        "depends_on": [],
    }


def initial_body(ticket_slug: str, ticket_alias: str) -> str:
    return (
        "# Verification\n\n"
        f"**Parent ticket**: [[{ticket_alias}]]\n\n"
        "**Status**: active (gates accumulating)\n\n"
        "_This document accumulates per-gate verification findings across "
        "the V-phase's five gates (D-review, P-review, I-per-slice, "
        "final-integration, PR-review). Findings are appended as each gate "
        "fires. The verdict is BINARY (PROCEED / BLOCKED) per Lock 11.4 — "
        "there is no 'PROCEED_WITH_NOTES' middle option. Severity-driven "
        "blocking: Critical/High auto-BLOCK; Medium BLOCKS unless waived; "
        "Low/Suggestion are non-blocking. The doc is considered finalized "
        "at V-completion (after final-integration or PR-review) — "
        "discipline-based, not filesystem-enforced._\n\n"
        "## Gates\n\n"
    )


def format_finding(finding: dict[str, Any]) -> str:
    """Render one finding as a markdown block."""
    severity = finding["severity"]
    initial = SEVERITY_INITIALS[severity]
    fid = finding["id"]
    title = finding["title"]
    location = finding["location"]
    desc = finding["finding"]
    fix = finding["fix"]
    impact = finding.get("impact")
    scope = finding.get("scope", "this-impl")
    user_waived = finding.get("user_waived", False)

    lines = [
        f"#### {initial}-{fid}: {title}",
        "",
        f"- **Severity**: {severity}",
        f"- **Location**: `{location}`",
        f"- **Finding**: {desc}",
        f"- **Fix recommendation**: {fix}",
    ]
    if impact:
        lines.append(f"- **Impact**: {impact}")
    if scope == "codebase-wide":
        lines.append(
            "- **Scope**: codebase-wide _(exceeds this implementation's "
            "bounds; signal to future codebase-review workflow)_"
        )
    if user_waived:
        lines.append("- **User-waived**: yes (Medium finding explicitly waived)")
    lines.append("")
    return "\n".join(lines)


def format_angle(angle: dict[str, Any]) -> str:
    """Render one angle's result + findings as a markdown block."""
    name = angle["name"]
    mechanism = angle["mechanism"]
    mech_label = (
        "fitness function" if mechanism == "fitness-function" else "LLM"
    )
    result = angle["result"]
    detail = angle.get("detail", "")
    findings = angle["findings"]

    lines = [
        f"### Angle: {name} ({mech_label})",
        "",
        f"**Result**: {result}",
    ]
    if detail:
        lines.append("")
        lines.append(detail)
    if findings:
        lines.append("")
        lines.append(f"**Findings ({len(findings)}):**")
        lines.append("")
        for f in findings:
            lines.append(format_finding(f))
    else:
        lines.append("")
        lines.append("_No findings from this angle._")
        lines.append("")
    return "\n".join(lines)


def format_gate_section(
    findings: dict[str, Any],
    timestamp: str,
) -> str:
    """Render the gate's full section as appended to the verification doc."""
    gate = findings["gate"]
    slice_id = findings.get("slice_id")
    verdict = findings["verdict"]
    summary = findings["summary"]
    loop_back = findings.get("loop_back_target")
    angles = findings["angles"]
    next_steps = findings.get("next_steps", [])

    header = f"## Gate: {gate}"
    if slice_id:
        header = f"## Gate: {gate} (slice {slice_id})"

    # Aggregate finding counts by severity for the gate header
    counts = {sev: 0 for sev in VALID_SEVERITIES}
    for angle in angles:
        for f in angle["findings"]:
            counts[f["severity"]] += 1
    counts_line = ", ".join(
        f"{sev[0]}={counts[sev]}" for sev in VALID_SEVERITIES
    )

    lines = [
        header,
        "",
        f"**Run at**: {timestamp}",
        f"**Verdict**: **{verdict}**",
        f"**Findings**: {counts_line}",
    ]
    if loop_back:
        lines.append(f"**Loop-back target**: {loop_back}")
    lines.append("")
    lines.append(f"**Summary**: {summary}")
    lines.append("")

    for angle in angles:
        lines.append(format_angle(angle))

    if next_steps:
        lines.append("### Next steps")
        lines.append("")
        for step in next_steps:
            lines.append(f"- {step}")
        lines.append("")

    return "\n".join(lines)


def append_to_doc(doc_path: Path, gate_block: str) -> None:
    """Append a gate's section to an existing verification doc.

    Preserves frontmatter and existing body content. Inserts the gate
    block at the end of the body (after a separating blank line).
    """
    content = doc_path.read_text()
    match = FRONTMATTER_RE.match(content)
    if not match:
        die(
            f"Existing verification doc {doc_path} has no parseable "
            "frontmatter. Refusing to append blindly. Inspect manually.",
            code=2,
        )

    fm_text = match.group("fm")
    body = match.group("body").rstrip()

    new_body = body + "\n\n" + gate_block

    doc_path.write_text(f"---\n{fm_text}\n---\n{new_body}")


def main() -> int:
    args = parse_args()

    findings_path = Path(args.findings).expanduser().resolve()
    findings = load_findings(findings_path)

    meta = run_thoughts_metadata()
    short = short_date(meta["date"])

    # ISO 8601 timestamp for the gate's run-time
    timestamp = (
        datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    )

    gate_block = format_gate_section(findings, timestamp)

    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    if not bundle_dir.exists() or not bundle_dir.is_dir():
        die(f"Bundle directory {bundle_dir} does not exist or is not a directory.")

    canonical_alias = f"verification-{short}-{args.ticket_slug}"
    doc_path = bundle_dir / f"{canonical_alias}.md"

    if args.stdout_only:
        print(gate_block)
        return 0

    if doc_path.exists():
        append_to_doc(doc_path, gate_block)
        appended = True
    else:
        fm = build_initial_frontmatter(
            meta,
            ticket_slug=args.ticket_slug,
            ticket_alias=args.ticket_alias,
            canonical_alias=canonical_alias,
        )
        doc_path.write_text(
            emit_frontmatter(fm)
            + "\n"
            + initial_body(args.ticket_slug, args.ticket_alias)
            + gate_block
        )
        appended = False

    print(
        json.dumps(
            {
                "verification_doc": str(doc_path),
                "gate": findings["gate"],
                "verdict": findings["verdict"],
                "loop_back_target": findings.get("loop_back_target"),
                "appended": appended,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
