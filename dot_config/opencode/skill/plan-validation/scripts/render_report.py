# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Render validation report from structured JSON findings.

Usage: uv run render_report.py <findings.json> [--output-dir <dir>]
       echo '{"plan": "..."}' | uv run render_report.py - [--output-dir <dir>]

Options:
  --output-dir <dir>  Save report to directory with auto-generated filename
                      If omitted, prints to stdout

Output: Markdown validation report

Input JSON Schema:
{
  "plan": "plan-alias",
  "plan_path": "path/to/plan.md",
  "phase": 1,
  "phase_title": "Phase Title",
  "branch": "branch-name",
  "commit": "abc1234",
  "verdict": "PROCEED | PROCEED WITH NOTES | BLOCKED",
  "summary": "Overall assessment",
  "code_review": {
    "critical": [{"title": "...", "file": "path:line", "issue": "...", "scenario": "...", "fix": "..."}],
    "warnings": [{"title": "...", "file": "path:line", "issue": "...", "conditions": "..."}],
    "suggestions": ["suggestion text"],
    "patterns": {"passed": ["pattern1"], "concerns": ["concern1"]}
  },
  "plan_validation": {
    "checks": {
      "tests": {"result": "pass|fail", "detail": "665 pass, 0 fail"},
      "types": {"result": "pass|fail", "detail": "clean"},
      "lint": {"result": "pass|fail", "detail": "2 warnings"}
    },
    "steps": [{"id": "1.1", "description": "...", "status": "complete|partial|missing"}],
    "deviations": [{"file": "path:line", "planned": "...", "actual": "...", "assessment": "improvement|concern"}],
    "manual_tests": ["test case 1", "test case 2"]
  },
  "next_steps": ["step 1", "step 2"]
}
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


def render_verdict_section(data: dict) -> str:
    """Render the verdict section."""
    return f"""## Verdict: {data["verdict"]}

**Summary**: {data.get("summary", "No summary provided.")}
"""


def render_critical_issues(issues: list) -> str:
    """Render critical issues."""
    if not issues:
        return "No critical issues found."

    lines = []
    for issue in issues:
        lines.append(f"""#### {issue.get("title", "Untitled Issue")}
- **File**: `{issue.get("file", "unknown")}`
- **Issue**: {issue.get("issue", "No description")}
- **Scenario**: {issue.get("scenario", "Not specified")}
- **Fix**: {issue.get("fix", "Not specified")}
""")
    return "\n".join(lines)


def render_warnings(warnings: list) -> str:
    """Render warnings."""
    if not warnings:
        return "No warnings."

    lines = []
    for warning in warnings:
        lines.append(f"""#### {warning.get("title", "Untitled Warning")}
- **File**: `{warning.get("file", "unknown")}`
- **Issue**: {warning.get("issue", "No description")}
- **Conditions**: {warning.get("conditions", "Not specified")}
""")
    return "\n".join(lines)


def render_suggestions(suggestions: list) -> str:
    """Render suggestions."""
    if not suggestions:
        return "No suggestions."

    return "\n".join(f"- {s}" for s in suggestions)


def render_patterns(patterns: dict) -> str:
    """Render pattern compliance."""
    lines = []
    for p in patterns.get("passed", []):
        lines.append(f"- ✓ {p}")
    for c in patterns.get("concerns", []):
        lines.append(f"- ⚠️ {c}")
    return "\n".join(lines) if lines else "- ✓ No pattern issues detected"


def render_code_review(code_review: dict) -> str:
    """Render code review section."""
    return f"""## Part 1: Code Review Findings

### Critical Issues (🔴)

{render_critical_issues(code_review.get("critical", []))}

### Warnings (🟠)

{render_warnings(code_review.get("warnings", []))}

### Suggestions (🟡)

{render_suggestions(code_review.get("suggestions", []))}

### Pattern Compliance

{render_patterns(code_review.get("patterns", {}))}
"""


def render_checks_table(checks: dict) -> str:
    """Render automated checks table."""
    rows = []

    check_commands = {
        "tests": "bun test",
        "types": "bun run typecheck",
        "lint": "bun run lint",
    }

    for name, cmd in check_commands.items():
        check = checks.get(name, {})
        result = check.get("result", "unknown")
        detail = check.get("detail", "")
        result_symbol = (
            "✓ Pass"
            if result == "pass"
            else "✗ Fail"
            if result == "fail"
            else "? Unknown"
        )
        rows.append(f"| {name.title()} | `{cmd}` | {result_symbol} | {detail} |")

    return """| Check | Command | Result | Notes |
|-------|---------|--------|-------|
""" + "\n".join(rows)


def render_steps_table(steps: list) -> str:
    """Render implementation status table."""
    if not steps:
        return "No steps defined in plan."

    rows = []
    status_symbols = {
        "complete": "✓ Complete",
        "partial": "⚠️ Partial",
        "missing": "✗ Missing",
    }

    for step in steps:
        status = status_symbols.get(step.get("status", "unknown"), "? Unknown")
        rows.append(
            f"| {step.get('id', '?')} | {step.get('description', 'No description')} | {status} |"
        )

    return """| Step | Description | Status |
|------|-------------|--------|
""" + "\n".join(rows)


def render_deviations_table(deviations: list) -> str:
    """Render deviations table."""
    if not deviations:
        return "Implementation matches plan specification."

    rows = []
    for dev in deviations:
        assessment = (
            "✓ Improvement" if dev.get("assessment") == "improvement" else "⚠️ Concern"
        )
        rows.append(
            f"| `{dev.get('file', '?')}` | {dev.get('planned', '?')} | {dev.get('actual', '?')} | {assessment} |"
        )

    return """| File:Line | Plan Specified | Actual Implementation | Assessment |
|-----------|----------------|----------------------|------------|
""" + "\n".join(rows)


def render_manual_tests(tests: list) -> str:
    """Render manual tests checklist."""
    if not tests:
        return "No manual testing required."

    return "\n".join(f"- [ ] {t}" for t in tests)


def render_plan_validation(plan_validation: dict) -> str:
    """Render plan validation section."""
    return f"""## Part 2: Plan Validation Findings

### Automated Checks

{render_checks_table(plan_validation.get("checks", {}))}

### Implementation Status

{render_steps_table(plan_validation.get("steps", []))}

### Deviations from Plan

{render_deviations_table(plan_validation.get("deviations", []))}

### Manual Testing Required

{render_manual_tests(plan_validation.get("manual_tests", []))}
"""


def render_next_steps(data: dict) -> str:
    """Render next steps based on verdict."""
    verdict = data.get("verdict", "BLOCKED")
    steps = data.get("next_steps", [])

    if not steps:
        if verdict == "PROCEED":
            steps = ["Proceed to next phase"]
        elif verdict == "PROCEED WITH NOTES":
            steps = ["Address noted items when convenient", "Proceed to next phase"]
        else:
            steps = ["Fix blocking issues", "Re-run validation"]

    steps_md = "\n".join(f"- [ ] {s}" for s in steps)

    return f"""## Next Steps

{steps_md}
"""


def render_report(data: dict) -> str:
    """Render the full validation report."""
    now = datetime.now(timezone.utc).isoformat()

    header = f"""# Validation Report: {data.get("plan", "Unknown Plan")} - Phase {data.get("phase", "?")}

**Plan**: [[{data.get("plan", "unknown")}]]
**Phase**: {data.get("phase", "?")} - {data.get("phase_title", "Unknown")}
**Branch**: {data.get("branch", "unknown")}
**Commit**: {data.get("commit", "unknown")}
**Date**: {now}

---

"""

    verdict = render_verdict_section(data)
    code_review = render_code_review(data.get("code_review", {}))
    plan_validation = render_plan_validation(data.get("plan_validation", {}))
    next_steps = render_next_steps(data)

    footer = f"""
---

**Validation completed**: {now}
"""

    return (
        header
        + verdict
        + "\n---\n\n"
        + code_review
        + "\n---\n\n"
        + plan_validation
        + "\n---\n\n"
        + next_steps
        + footer
    )


def generate_filename(data: dict) -> str:
    """Generate filename from plan, phase, and timestamp."""
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    # Sanitize plan name for filename
    plan = data.get("plan", "unknown")
    plan_slug = re.sub(r"[^a-zA-Z0-9-]", "-", plan.lower())
    plan_slug = re.sub(r"-+", "-", plan_slug).strip("-")

    phase = data.get("phase", "0")

    return f"{timestamp}_{plan_slug}-phase-{phase}-validation.md"


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: uv run render_report.py <findings.json> [--output-dir <dir>]",
            file=sys.stderr,
        )
        print(
            "       echo '{...}' | uv run render_report.py - [--output-dir <dir>]",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse arguments
    input_file = sys.argv[1]
    output_dir = None

    if "--output-dir" in sys.argv:
        idx = sys.argv.index("--output-dir")
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]
        else:
            print("Error: --output-dir requires a directory path", file=sys.stderr)
            sys.exit(1)

    # Load input
    if input_file == "-":
        data = json.load(sys.stdin)
    else:
        with open(input_file, "r") as f:
            data = json.load(f)

    # Render report
    report = render_report(data)

    # Output
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        filename = generate_filename(data)
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "w") as f:
            f.write(report)

        # Print path to stderr so caller knows where it went
        print(f"Saved: {output_path}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
