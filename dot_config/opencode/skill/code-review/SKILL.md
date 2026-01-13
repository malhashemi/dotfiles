---
name: code-review
description: |
  Reviews code changes for bugs, security issues, and adherence to codebase patterns. This skill
  should be used when reviewing diffs, commits, branches, or pull requests. It focuses on finding
  real bugs (not style nitpicks), verifying code fits existing patterns, and providing actionable
  feedback with clear severity levels.
---

# Code Review

## Overview

Review code changes to find bugs, security issues, and pattern violations. Focus on what matters:
logic errors, edge cases, and whether the code fits the codebase. Avoid style zealotry.

## When to Use

- Reviewing uncommitted changes (staged or unstaged)
- Reviewing a specific commit
- Comparing branches
- Reviewing a pull request
- As part of a validation gate between implementation phases

## Determining What to Review

Based on input, determine which type of review to perform:

| Input | How to Get Diff |
|-------|-----------------|
| No arguments (default) | `git diff` (unstaged) + `git diff --cached` (staged) |
| Commit hash (SHA) | `git show <hash>` |
| Branch name | `git diff <branch>...HEAD` |
| PR URL or number | `gh pr view` + `gh pr diff` |

## Gathering Context

**Diffs alone are not enough.** After getting the diff, read the entire file(s) being modified
to understand the full context. Code that looks wrong in isolation may be correct given
surrounding logic—and vice versa.

1. Use the diff to identify which files changed
2. Read the full file to understand existing patterns, control flow, and error handling
3. Check for existing conventions files (`CONVENTIONS.md`, `AGENTS.md`, `.editorconfig`, etc.)

## What to Look For

### Bugs (Primary Focus)

- **Logic errors** - Off-by-one mistakes, incorrect conditionals
- **If-else guards** - Missing guards, incorrect branching, unreachable code paths
- **Edge cases** - Null/empty/undefined inputs, error conditions, race conditions
- **Security issues** - Injection, auth bypass, data exposure
- **Broken error handling** - Swallowed failures, unexpected throws, uncaught error types

### Structure (Does the code fit?)

- Does it follow existing patterns and conventions?
- Are there established abstractions it should use but doesn't?
- Excessive nesting that could be flattened with early returns or extraction

### Performance (Only if obviously problematic)

- O(n²) on unbounded data
- N+1 queries
- Blocking I/O on hot paths

## Before Flagging Something

**Be certain.** If calling something a bug, be confident it actually is one.

### Do

- Only review the changes - do not review pre-existing code that wasn't modified
- Investigate before flagging - if unsure, look deeper first
- Explain realistic scenarios where edge cases actually break things

### Don't

- Flag something as a bug if unsure
- Invent hypothetical problems without realistic scenarios
- Be a zealot about style

### Style Violations - Be Reasonable

- Verify the code is actually in violation before complaining
- Some "violations" are acceptable when they're the simplest option
- A `let` statement is fine if the alternative is convoluted
- Excessive nesting is a legitimate concern regardless of other style choices
- Don't flag style preferences unless they clearly violate established project conventions

## Research Before Flagging

Use available tools to verify before claiming something is wrong:

| Tool | Use For |
|------|---------|
| `codebase-pattern-finder` | Find how existing code handles similar problems |
| `codebase-analyzer` | Understand existing patterns and conventions |
| Web search | Verify correct usage of libraries/APIs |

If uncertain and can't verify, say **"I'm not sure about X"** rather than flagging as definite.

## Output Guidelines

### Tone

- Matter-of-fact, not accusatory or overly positive
- Reads as helpful AI assistant, not human reviewer pretending
- Write so reader can quickly understand without reading too closely

### Content

- **Be direct** about bugs - clearly explain why it's a bug
- **Communicate severity accurately** - do not overstate
- **Explain conditions** - clearly state scenarios/inputs necessary for bug to arise
- **No flattery** - avoid "Great job...", "Thanks for..."

### Severity Levels

| Level | Meaning |
|-------|---------|
| 🔴 **Critical** | Will cause failures, security vulnerability, data loss |
| 🟠 **Warning** | Could cause issues under specific conditions |
| 🟡 **Suggestion** | Improvement opportunity, not a bug |

## Output Template

```markdown
## Code Review: [scope description]

### Summary

[1-2 sentences: Overall assessment - clean, minor issues, or significant concerns]

### Issues Found

#### 🔴 [Critical Issue Title]
**File:** `path/to/file.ts:line`
**Issue:** [Clear description of the bug]
**Scenario:** [When/how this breaks]
**Suggested fix:** [How to fix it]

#### 🟠 [Warning Title]
**File:** `path/to/file.ts:line`
**Issue:** [Description]
**Conditions:** [When this becomes a problem]

#### 🟡 [Suggestion Title]
**File:** `path/to/file.ts:line`
**Suggestion:** [What could be improved and why]

### Patterns Checked

- ✓ Follows existing error handling patterns
- ✓ Uses established abstractions
- ⚠️ Inconsistent with [pattern] in [other file]

### Verdict

[PASS | PASS WITH NOTES | NEEDS CHANGES]

[If needs changes: list what must be fixed before approval]
```
