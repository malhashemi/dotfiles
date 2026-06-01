# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml>=6.0",
# ]
# ///
"""
render-design-doc-skeleton.py — Render the D-phase design doc skeleton.

Invoked by the `code-design` skill as its first step when entering D-phase.
Overwrites the body of the design.md placeholder (created at orient-time by
scaffold-implementation-bundle.py) with a richer, context-aware skeleton that:

  1. References the bundle's research file (if present), so the design
     conversation starts grounded in R-phase findings rather than blank.
  2. Includes section-specific prompts informed by the parent ticket's
     primary tag (feature/bug/exploration/hotfix/infrastructure/chore).
  3. Transitions the design doc from status: draft (scaffold) to status:
     active (D-phase in progress).
  4. Preserves the design doc's frontmatter; replaces only the body.

The design doc has three sections per spec Lock 6:

  1. Current state          — grounding from R findings; what the touched
                              area currently looks like; patterns and
                              invariants that exist
  2. Desired end state      — what the solved problem looks like in the
                              codebase after implementation; behavioral
                              and structural end-state
  3. Design decisions       — architectural choices with rationale;
                              type/interface decisions; vertical-slice
                              identification; risk areas; multi-plan
                              identification (if architecturally large)

D-phase is always-interactive (per Lock 6): the agent presents this
skeleton, human brain-surgeries via Question tool per substantive
decision, iterate until aligned. The skeleton is a scaffold for that
conversation — NOT a fill-in-the-blank form.

Usage:
    uv run render-design-doc-skeleton.py \\
        --design-file <path> \\
        --primary-tag <feature|bug|exploration|hotfix|infrastructure|chore> \\
        [--research-file <path>]

Arguments:
    --design-file     Path to the design.md placeholder previously created
                      by scaffold-implementation-bundle.py. Body is
                      overwritten; frontmatter is preserved (with the
                      status field flipped to 'active' and last_updated_*
                      refreshed).
    --primary-tag     The parent ticket's primary tag. Drives the
                      tag-specific guidance inside each section.
    --research-file   (Optional) Path to the bundle's research file (or a
                      synthesized R-phase doc). If present, the skeleton
                      references it inline in the Current state section
                      so the agent grounds the D-phase conversation in
                      already-gathered facts.

Exit codes:
    0  Success
    1  Validation error (bad args, invalid tag, missing design file, no
       frontmatter in design file)
    2  Environment error (thoughts CLI not on PATH, metadata parse failed)

Output (stdout): JSON object confirming the render:
    {
      "design_file": "/.../design-2026-05-17-team-workspaces.md",
      "primary_tag": "feature",
      "research_referenced": true,
      "status_before": "draft",
      "status_after": "active"
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

VALID_PRIMARY_TAGS = {
    "feature",
    "bug",
    "exploration",
    "hotfix",
    "infrastructure",
    "chore",
}

FRONTMATTER_RE = re.compile(
    r"\A---\r?\n(?P<fm>.*?)\r?\n---\r?\n(?P<body>.*)\Z",
    re.DOTALL,
)


# Tag-specific guidance for each design section. The text seeds the
# brain-surgery conversation; the agent expands during D-phase.
TAG_GUIDANCE = {
    "feature": {
        "current_state": (
            "Map the existing capability surface that this feature builds "
            "on or replaces. Name the modules, types, and seams the feature "
            "touches. Cite specific file:line references from the research "
            "file. Do NOT describe the entire codebase — only the touched "
            "area and its immediate context."
        ),
        "desired_end_state": (
            "Describe the system after this feature ships. Cover behavioral "
            "end-state (per ticket AC) AND structural end-state (new types, "
            "new module boundaries, API contract additions). The reader "
            "should be able to picture the new code shape without seeing "
            "the code."
        ),
        "design_decisions": (
            "Capture each load-bearing decision with one-line rationale. "
            "Features usually surface 3-7 decisions: type/interface shape, "
            "data-flow direction, ownership of cross-cutting concerns, "
            "extension points. Identify vertical slices (each independently "
            "committable + testable). If the work is architecturally large, "
            "list multiple plans here (per Lock 6: multiple plans, NOT "
            "multiple sub-tickets)."
        ),
    },
    "bug": {
        "current_state": (
            "Reproduce the bug in narrative form: which inputs, which code "
            "path, which invariant violated. Cite the failing test or "
            "reproduction harness. If R-phase used the diagnose-feedback-loop "
            "pattern, summarize the feedback loop here. Stay focused on "
            "the bug surface; do NOT describe adjacent unaffected code."
        ),
        "desired_end_state": (
            "Describe the system after the fix. The fix should target ROOT "
            "CAUSE, not symptom — name the root cause and the invariant the "
            "fix restores. Reproduction no longer triggers the bug; "
            "regression test added; adjacent failure paths unchanged."
        ),
        "design_decisions": (
            "Bugs usually surface 1-3 decisions: where the fix lives (which "
            "layer), whether to fix the symptom or refactor for prevention, "
            "regression test seam selection. Identify the smallest vertical "
            "slice that ships the fix. Hotfix-tier scope creep is the "
            "biggest risk — stay disciplined."
        ),
    },
    "exploration": {
        "current_state": (
            "Frame what is currently UNKNOWN that this spike investigates. "
            "Cite R-phase findings that surface the gap. Do NOT pretend "
            "the answer is already known."
        ),
        "desired_end_state": (
            "Describe the artifacts the spike will produce (research doc "
            "updates, prototype runnable, DR if the spike concludes with a "
            "hard-to-reverse choice). What decision does the spike's output "
            "ENABLE? If the spike fails to conclude, what does the partial "
            "finding look like?"
        ),
        "design_decisions": (
            "Spikes surface time-box, decision points, and (often) prototype "
            "strategy. The output is INFORMATION — capture what shape that "
            "information takes."
        ),
    },
    "hotfix": {
        "current_state": (
            "Incident description: what's broken in production, blast radius, "
            "customer impact, when started. Cite the incident channel or "
            "report. Stay TERSE — hotfix is time-sensitive."
        ),
        "desired_end_state": (
            "Describe the system after the fix lands AND is verified in "
            "production. Include the verification signal (monitoring metric, "
            "customer report, direct test) that confirms incident "
            "resolution."
        ),
        "design_decisions": (
            "Hotfix decisions: minimal-change scope, rollback plan, "
            "verification signal. Postmortem ticket placeholder if not yet "
            "created. NO scope creep — hotfix is STOP THE BLEEDING, not "
            "comprehensive correctness."
        ),
    },
    "infrastructure": {
        "current_state": (
            "Map the infrastructure baseline: what exists now (or doesn't), "
            "which services, configs, dependencies, vendors. Cite the "
            "research file for vendor comparisons or capability matrices."
        ),
        "desired_end_state": (
            "Describe the target infrastructure: services running, configs "
            "applied, dependencies installed, verification signal (terraform "
            "plan clean / health endpoint 200 / build step exit 0)."
        ),
        "design_decisions": (
            "Infrastructure decisions are often DR-worthy (vendor choice, "
            "architecture pattern, technology choice, boundary decision). "
            "Surface DR opportunities here. Capture rollback plan, cost "
            "implications, security review status, monitoring/observability "
            "setup."
        ),
    },
    "chore": {
        "current_state": (
            "Name the specific surface to change (file, field, configuration). "
            "Cite file:line. Chores are mechanical — keep this section "
            "small."
        ),
        "desired_end_state": (
            "Describe the change applied: field renamed, dependency bumped, "
            "doc updated. Verification: grep confirms the change is "
            "consistent; no regressions in adjacent tests."
        ),
        "design_decisions": (
            "Chores rarely surface design decisions. If a decision DOES "
            "surface during D-phase (e.g., a rename touches more than "
            "expected), the work probably isn't actually a chore — "
            "consider re-tagging."
        ),
    },
}


def die(msg: str, code: int = 1) -> None:
    """Print an error to stderr and exit."""
    print(f"render-design-doc-skeleton: {msg}", file=sys.stderr)
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
        description="Render the D-phase design doc skeleton.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--design-file",
        required=True,
        help="Path to the design.md placeholder file.",
    )
    parser.add_argument(
        "--primary-tag",
        required=True,
        choices=sorted(VALID_PRIMARY_TAGS),
        help="The parent ticket's primary tag.",
    )
    parser.add_argument(
        "--research-file",
        required=False,
        help=(
            "Optional path to the bundle's research file. If present, the "
            "skeleton references it in the Current state section."
        ),
    )
    return parser.parse_args()


def split_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Split a file's content into (frontmatter dict, body string)."""
    match = FRONTMATTER_RE.match(content)
    if not match:
        die(
            "Design file does not start with a YAML frontmatter block. "
            "Expected the file to begin with `---` on its own line, followed "
            "by YAML, then `---` on its own line. Was the file created by "
            "scaffold-implementation-bundle.py?"
        )
        return {}, ""  # unreachable

    fm_text = match.group("fm")
    body = match.group("body")

    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        die(f"Design file frontmatter YAML is malformed: {exc}")
        return {}, ""  # unreachable

    if not isinstance(fm, dict):
        die(
            f"Design file frontmatter must be a YAML mapping; found "
            f"{type(fm).__name__}."
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


def build_body(
    primary_tag: str,
    parent_alias: str,
    research_alias: str | None,
) -> str:
    """Build the rich design-doc body for the given primary tag."""
    guidance = TAG_GUIDANCE[primary_tag]

    research_pointer = ""
    if research_alias:
        research_pointer = (
            f"\n_Grounding: [[{research_alias}]] — R-phase findings already "
            "gathered. Cite specific file:line references inline rather than "
            "re-paraphrasing entire sections._\n"
        )
    else:
        research_pointer = (
            "\n_No R-phase research file referenced. If R-phase has produced "
            "findings, code-design should re-invoke this script with "
            "--research-file pointing at the synthesized research artifact._\n"
        )

    return (
        "# Design\n\n"
        f"**Parent ticket**: [[{parent_alias}]]\n\n"
        f"**Primary tag**: `{primary_tag}`\n\n"
        "**Status**: active (D-phase in progress)\n"
        + research_pointer
        + "\n"
        "_D-phase is the highest-leverage stage of the implementation "
        "workflow (per Lock 6). The brain-surgery alignment conversation "
        "happens by default, not by incantation. The agent presents this "
        "skeleton; the human stress-tests via Question tool per substantive "
        "decision; iterate until aligned. Each section's guidance below is "
        "context for the conversation — not a fill-in-the-blank form._\n\n"
        "## Current state\n\n"
        f"_Guidance ({primary_tag})_: {guidance['current_state']}\n\n"
        "_(populated by code-design through brain-surgery conversation)_\n\n"
        "## Desired end state\n\n"
        f"_Guidance ({primary_tag})_: {guidance['desired_end_state']}\n\n"
        "_(populated by code-design through brain-surgery conversation)_\n\n"
        "## Design decisions\n\n"
        f"_Guidance ({primary_tag})_: {guidance['design_decisions']}\n\n"
        "_(populated by code-design through brain-surgery conversation)_\n\n"
        "### Multi-plan identification\n\n"
        "_If this design surfaces multiple architecturally-distinct plans, "
        "list them here with one-line scopes. The code-plan skill produces "
        "one plan doc per plan listed here. Default: one plan per design "
        "(most designs)._\n\n"
        "### Vertical slices\n\n"
        "_Each slice MUST be independently committable + testable. List "
        "slices in dependency order. The code-structure skill takes this "
        "list and produces the structural skeleton (files + signatures + "
        "test structure) per slice._\n\n"
        "### Risk areas\n\n"
        "_Where friction is most likely during I-phase. Evidence-bound: "
        "cite research findings or code references._\n"
    )


def main() -> int:
    args = parse_args()

    design_path = Path(args.design_file).expanduser().resolve()
    if not design_path.exists():
        die(
            f"Design file {design_path} does not exist. Was the bundle "
            "scaffolded? scaffold-implementation-bundle.py should have "
            "created it during orient."
        )
    if not design_path.is_file():
        die(f"{design_path} is not a regular file.")

    research_alias: str | None = None
    if args.research_file:
        research_path = Path(args.research_file).expanduser().resolve()
        if not research_path.exists():
            die(
                f"Research file {research_path} does not exist. Omit "
                "--research-file if R-phase has not produced one yet."
            )
        # Extract the canonical alias from the research file's frontmatter
        research_content = research_path.read_text()
        research_fm, _ = split_frontmatter(research_content)
        aliases = research_fm.get("aliases", [])
        if aliases and isinstance(aliases, list) and aliases:
            research_alias = aliases[0]
        else:
            die(
                f"Research file {research_path} has no `aliases:` in "
                "frontmatter. Cannot reference it cleanly from the design "
                "doc. Inspect the research file manually."
            )

    meta = run_thoughts_metadata()
    content = design_path.read_text()
    fm, _ = split_frontmatter(content)

    parent_value = fm.get("parent", "")
    if isinstance(parent_value, str) and parent_value.startswith("[[") and parent_value.endswith("]]"):
        parent_alias = parent_value[2:-2]
    elif isinstance(parent_value, str) and parent_value:
        parent_alias = parent_value
    else:
        die(
            f"Design file {design_path} frontmatter has no `parent:` field "
            "or it is empty. Expected a [[ticket-alias]] reference."
        )

    status_before = fm.get("status", "(none)")

    # Update frontmatter: flip status to active, refresh last_updated metadata
    fm["status"] = "active"
    fm["last_updated"] = meta["date"]
    fm["last_updated_by"] = meta["owner"]
    fm["last_updated_note"] = (
        f"D-phase started; skeleton rendered with {args.primary_tag}-tag "
        "guidance"
        + (f"; grounded in [[{research_alias}]]" if research_alias else "")
        + "."
    )

    new_body = build_body(args.primary_tag, parent_alias, research_alias)

    design_path.write_text(emit_frontmatter(fm) + "\n" + new_body)

    print(
        json.dumps(
            {
                "design_file": str(design_path),
                "primary_tag": args.primary_tag,
                "research_referenced": research_alias is not None,
                "status_before": status_before,
                "status_after": "active",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
