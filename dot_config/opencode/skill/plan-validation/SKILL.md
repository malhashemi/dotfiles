---
name: plan-validation
description: |
  Validates implementation plan execution by verifying success criteria and identifying deviations.
  This skill should be used after a phase or plan has been implemented and committed. It runs
  automated checks (tests, types, lint), compares actual changes against the plan's specifications,
  and generates a validation report documenting what was completed, what deviated, and what needs
  manual testing.
---

# Plan Validation

## Overview

Validate that an implementation plan phase was correctly executed by running automated checks,
comparing changes against the plan's specifications, and generating a validation report that
documents completion status, deviations, and required manual testing.

## When to Use

- After implementing a phase from an implementation plan
- After committing changes for a phase (validation works best with commits to analyze)
- Before proceeding to the next phase (as a gate check)
- When asked to verify or validate implementation work

## Scripts

The base directory for this skill is provided when loaded.

### Via Justfile

```bash
just -f {base_dir}/justfile <recipe> [args...]
```

| Recipe | Arguments | Description |
|--------|-----------|-------------|
| `render` | `findings.json` | Render to stdout |
| `render-stdin` | - | Render from piped JSON to stdout |
| `save` | `findings.json output_dir` | Save with auto-generated filename |
| `save-stdin` | `output_dir` | Pipe JSON, save to directory |
| `schema` | - | Show the expected JSON schema |

### Direct Execution

```bash
uv run {base_dir}/scripts/render_report.py <findings.json> [--output-dir <dir>]
```

### Examples

```bash
# Render to stdout, redirect to file
just -f {base_dir}/justfile render /tmp/findings.json > thoughts/shared/validate/report.md

# Render from stdin
echo '{"plan": "..."}' | just -f {base_dir}/justfile render-stdin > report.md

# Save with auto-generated filename (use absolute path)
just -f {base_dir}/justfile save /tmp/findings.json /absolute/path/to/validate/

# Direct execution with output directory
uv run {base_dir}/scripts/render_report.py findings.json --output-dir thoughts/shared/validate
```

**Note**: When using `save` recipes, pass an absolute path for `output_dir` to ensure correct placement.

## Required Inputs

To validate a plan phase, the following information is needed:

| Input | Description | Example |
|-------|-------------|---------|
| Plan path | Location of the implementation plan | `thoughts/shared/plans/2026-01-03_core-graph-validation-fixes.md` |
| Phase number | Which phase to validate | `Phase 1` |
| Worktree path | Working directory (if using worktrees) | `.trees/plan-1-core-graph` |

## Validation Workflow

### Step 1: Read the Plan Phase

1. Read the full implementation plan
2. Locate the specific phase to validate
3. Extract:
   - What changes were specified
   - Success criteria (automated and manual)
   - Files that should have been modified

### Step 2: Gather Evidence

Run commands to understand what was implemented:

```bash
# Check recent commits
git log --oneline -n 10

# See what changed
git diff HEAD~N..HEAD  # Where N covers the phase's commits

# Check current status
git status
```

### Step 3: Run Automated Verification

Execute the success criteria commands from the plan. Common patterns:

```bash
# TypeScript/JavaScript projects
bun test                    # Run tests
bun run typecheck          # Type checking
bun run lint               # Linting

# Or if using make
make check                  # Combined checks
make test                   # Tests only
make build                  # Build verification
```

Document each result as pass (✓) or fail (✗).

### Step 4: Compare Against Plan

For each item in the phase:

1. **Check completion claims** - If the plan marks something as done, verify the code exists
2. **Verify implementation matches spec** - Does the code do what the plan specified?
3. **Look for deviations** - Improvements, shortcuts, or missing pieces
4. **Assess edge cases** - Were error conditions handled?

Use codebase analysis as needed:
- `codebase-locator` to find modified files
- `codebase-analyzer` to examine implementation details
- `codebase-pattern-finder` to verify patterns were followed

### Step 5: Generate Validation Report

Structure findings as JSON and use the render script:

```json
{
  "plan": "plan-alias",
  "plan_path": "thoughts/shared/plans/...",
  "phase": 1,
  "phase_title": "Graph Logic Fixes",
  "branch": "implement/plan-1",
  "commit": "abc1234",
  "verdict": "PROCEED",
  "summary": "Phase 1 implemented correctly with all tests passing.",
  "code_review": {
    "critical": [],
    "warnings": [],
    "suggestions": ["Consider adding edge case test"],
    "patterns": {"passed": ["Error handling", "Naming conventions"], "concerns": []}
  },
  "plan_validation": {
    "checks": {
      "tests": {"result": "pass", "detail": "665 pass, 0 fail"},
      "types": {"result": "pass", "detail": "clean"},
      "lint": {"result": "pass", "detail": "no issues"}
    },
    "steps": [
      {"id": "1.1", "description": "Write failing tests", "status": "complete"},
      {"id": "1.2", "description": "Remove parent blocking", "status": "complete"}
    ],
    "deviations": [],
    "manual_tests": ["Verify backlog blocked shows correct count"]
  },
  "next_steps": ["Proceed to Phase 2"]
}
```

Then render:

```bash
just -f {base_dir}/justfile render findings.json > thoughts/shared/validate/report.md
```

## Validation Checklist

Always verify:

- [ ] All phase steps marked complete are actually implemented
- [ ] Automated tests pass (`bun test`)
- [ ] Type checking passes (`bun run typecheck`)
- [ ] Linting passes (`bun run lint`)
- [ ] Code follows existing codebase patterns
- [ ] No regressions introduced (existing tests still pass)
- [ ] Error handling is present and robust
- [ ] Success criteria from plan are met

## Report Output

The `render_report.py` script generates a structured markdown report with:

1. **Header** - Plan, phase, branch, commit, date
2. **Verdict** - PROCEED / PROCEED WITH NOTES / BLOCKED with summary
3. **Part 1: Code Review** - Critical issues, warnings, suggestions, pattern compliance
4. **Part 2: Plan Validation** - Automated checks table, implementation status, deviations, manual tests
5. **Next Steps** - Action items based on verdict

The script handles all formatting mechanically. Focus on gathering accurate findings in the JSON structure.

## After Validation

1. Save the report to `thoughts/shared/validate/`
2. Run `thoughts sync` to commit the validation report
3. Present findings to the user with:
   - Summary: Pass/Fail/Partial
   - Critical issues requiring attention
   - Path to full report
   - Recommendation: proceed or fix first
