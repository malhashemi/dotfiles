---
name: phase-execution
description: |
  Your bulletproof guide to executing implementation phases! Handles commits, detects when 
  phases are too big, and knows when to bail cleanly. Load this whenever you're implementing 
  a phase - it provides clean commit protocol and signals the orchestrator when things go sideways.
---

# Phase Execution

## Overview

Execute a single phase from an implementation plan with disciplined commit protocol and 
automatic detection of phases that are too large.

## When to Use

- When executing a phase from an implementation plan
- When the orchestrator (Planner) hands off a specific phase for implementation
- When working within the RPIV orchestration system

## Inputs

The orchestrator provides:

| Input | Description | Example |
|-------|-------------|---------|
| Plan path | Location of the implementation plan | `thoughts/shared/plans/2026-01-03_core-graph.md` |
| Phase number | Which phase to execute | `Phase 2` |
| Worktree path | Working directory (if using worktrees) | `.trees/plan-1-core-graph` |
| Branch name | Git branch for commits | `implement/plan-1-core-graph` |

## Execution Protocol

### Step 1: Read Phase Requirements

1. Read the full implementation plan
2. Locate the specific phase
3. Extract:
   - What changes are required (files, code patterns)
   - Success criteria (automated and manual)
   - Dependencies on previous phases
4. Verify previous phases are complete (check git log or plan checkboxes)

### Step 2: Execute Implementation

For each change in the phase:

1. Make the code change
2. Run relevant tests incrementally (don't wait until end)
3. If a test fails, fix immediately before proceeding
4. Track context consumption mentally

### Step 3: Escape Hatch Detection

**Trigger conditions** (any of these):
- Context threshold message received: "STOP IMMEDIATELY. Context threshold..."
- Significant scope creep detected (implementing things not in phase spec)
- Phase requires more than 3-4 significant file changes beyond what was specified

**Escape hatch protocol**:
```
1. STOP immediately
2. Discard uncommitted changes: git checkout .
3. Return to orchestrator with signal: "NEEDS_DECOMPOSITION"
4. Include: what was completed, what remains, estimated sub-phases
```

### Step 4: Commit Protocol

When phase is complete:

1. Stage all changes: `git add -A`
2. Create commit with structured message:
   ```
   Phase N: [Phase Title]
   
   - [Key change 1]
   - [Key change 2]
   
   Plan: thoughts/shared/plans/[plan-file].md
   ```
3. Push to branch: `git push origin [branch-name]`

### Step 5: Verification

Before returning to orchestrator:

1. Run ALL success criteria commands from the plan
2. Document results:
   - ✓ for passing checks
   - ✗ for failing checks (should abort, not return success)
3. Note any manual verification items for later

## Return Protocol

On successful completion:
```
PHASE_COMPLETE
Commit: [SHA]
Checks:
  - tests: ✓
  - types: ✓
  - lint: ✓
Manual verification needed:
  - [item 1]
  - [item 2]
```

On escape hatch trigger:
```
NEEDS_DECOMPOSITION
Completed:
  - [what was done]
Remaining:
  - [what remains]
  - [what remains]
Suggested sub-phases:
  - [sub-phase 1 description]
  - [sub-phase 2 description]
```

## Anti-Patterns

- **Don't batch all tests to the end** - Run tests incrementally
- **Don't commit partial work** - Either complete the phase or escape hatch
- **Don't ignore scope creep** - If you're doing more than specified, escape hatch
- **Don't continue after context warning** - The plugin message is authoritative
- **Don't update the plan file** - Return PHASE_COMPLETE and let the orchestrator handle progress tracking
- **Don't skip the push** - Always `git push` after committing; the orchestrator and validator need your commits on the remote
