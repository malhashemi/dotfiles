---
name: implementation-orchestration
description: |
  The Planner's guide to becoming an orchestrator! Manages the complete implementation lifecycle: 
  worktrees, branches, spawning Implement agents, validation gates, and decomposition triggers. 
  When ready to execute a plan, load this skill.
---

# Implementation Orchestration

## CRITICAL: You Are an Orchestrator, Not an Implementer

**NEVER** implement phases yourself. You do not write code, tests, or make commits.

**ALWAYS** spawn `implement` subagent for each phase via the Task tool.

Your job is to:
- Read and analyze plans
- Create worktrees and branches
- Spawn Implement agents (they do the actual work)
- Spawn Validator after each phase
- Track progress and update checkboxes
- Handle decomposition when needed

If you find yourself writing code, editing source files, or running test commands to verify your own changes — STOP. You are doing the Implement agent's job. Spawn an Implement agent instead.

---

## Overview

After creating a plan, the Planner becomes the orchestrator for that plan's implementation.
This skill provides the protocol for managing phases, worktrees, branches, validation,
and decomposition triggers.

## When to Use

- After plan is approved by Validator (via plan-review)
- When RPIV hands off a plan for implementation
- When managing multiple phases that may be sequential or parallel

## Prerequisites

1. Plan exists and is approved
2. Feature branch exists (e.g., `polish`)
3. Git working tree is clean

## Scripts

Execute via justfile or directly. The base directory is provided when skill is loaded.

| Recipe | Command | Purpose |
|--------|---------|---------|
| `worktree-create` | `just -f {base_dir}/justfile worktree-create {plan-slug} {base-branch}` | Create plan worktree |
| `worktree-cleanup` | `just -f {base_dir}/justfile worktree-cleanup {plan-slug}` | Remove worktree after merge |

## Orchestration Protocol

### Step 1: Setup Worktree

```bash
just -f {base_dir}/justfile worktree-create {plan-slug} {base-branch}
```

See `references/worktree-patterns.md` for naming conventions and git commands.

### Step 2: Analyze Phase Dependencies

Categorize phases:
- **Sequential**: One after another → commit to plan branch
- **Parallel**: Can run simultaneously → separate branches + worktrees
- **Blocked**: Waiting on dependency → defer until unblocked

### Step 3: Execute Phases

For each sequential phase, spawn Implement:

```
task({
  subagent_type: "implement",
  description: "Execute Phase N",
  prompt: "Execute Phase N from plan at [plan-path].
           Worktree: .trees/{plan-slug}
           Branch: implement/{plan-slug}
           Load skill(name='phase-execution') for protocol.
           Return PHASE_COMPLETE or NEEDS_DECOMPOSITION."
})
```

For parallel phases, issue multiple Task calls simultaneously with **separate worktrees**.

**CRITICAL: Parallel Work Isolation**

Parallel phases MUST have separate worktrees. Never run parallel sub-phases in the same 
worktree—they will conflict on file edits and git operations. Each parallel track needs:
- Its own worktree: `.trees/plan-N-phase-X`
- Its own branch: `implement/plan-N-phase-X`

### Step 4: Validation Gates

After each phase, validate. See `references/validation-gates.md` for:
- Validator spawning pattern
- Handling PROCEED / PROCEED_WITH_NOTES / BLOCKED
- RPIV trigger for decomposition

### Step 5: Progress Tracking

After successful phase completion and validation, update the plan document to reflect progress.
See the Progress Tracking section below for detailed guidance.

### Step 6: Plan Completion & PR Opening

1. Final validation with Validator
2. Create PR: `gh pr create --base {feature-branch} --head implement/{plan-slug}`
3. **Return to RPIV** with structured completion report (see below)

**CRITICAL**: Do NOT handle PR review yourself. Return to RPIV immediately after opening the PR.
RPIV orchestrates the PR review phase separately.

**Completion Report Format**:

```markdown
IMPLEMENTATION_COMPLETE

Plan: {plan-path}
PR: #{pr_number} - {pr_title}
URL: {pr_url}
Worktree: {worktree_path}
Branch: {branch}

Phases completed: {n}/{total}
Commits: {commit_count}
Tests: passing
Build: passing

Ready for PR review phase.
```

**After PR is merged** (RPIV will tell you when):
- `just -f {base_dir}/justfile worktree-cleanup {plan-slug}`

## Progress Tracking

**CRITICAL**: Only YOU (the orchestrator) update plan checkboxes. Implement agents do NOT 
touch the plan file—they return PHASE_COMPLETE and you record the progress.

After receiving PHASE_COMPLETE from Implement and PROCEED from Validator, update the plan 
to reflect what was accomplished. Use judgment to determine completion status.

### Checkbox Types in Plans

| Type | Format | When to Update |
|------|--------|----------------|
| Phase header | `## Phase 1: Title` → `## Phase 1: Title ✓` | All phase success criteria pass |
| Automated checks | `- [ ] Tests pass` | After running and confirming pass |
| Success criteria | `- [ ] File exists at path` | After verifying condition is met |
| Manual verification | `- [ ] Verify UI works` | After checking with available tools |

### Update Protocol

After receiving `PHASE_COMPLETE` from Implement and `PROCEED` from Validator:

1. **Mark phase header complete**: Add ✓ to phase header
   ```
   ## Phase 2: Core Implementation
   ```
   becomes:
   ```
   ## Phase 2: Core Implementation ✓
   ```

2. **Update success criteria checkboxes**: Change `[ ]` to `[x]` for verified items
   ```
   - [ ] All tests pass
   - [ ] TypeScript compiles without errors
   ```
   becomes:
   ```
   - [x] All tests pass
   - [x] TypeScript compiles without errors
   ```

3. **Handle manual verification items**: Attempt ALL verification, not just "automated" ones
   - Use available tools: browser automation, CLI tools, API calls, file checks
   - If verified successfully → mark `[x]`
   - If genuinely cannot verify → leave `[ ]` and note reason in commit or report

### Verification Approach

**Attempt everything.** The distinction is not "automated vs manual" but "can verify vs genuinely cannot."

Available verification methods:
- **CLI tools**: Run commands, check output, verify behavior
- **Browser automation**: Playwright, browser MCP for UI verification
- **API calls**: Test endpoints, verify responses
- **File system**: Check files exist, content matches expected
- **Process checks**: Verify services running, ports listening

Only defer verification when genuinely impossible (e.g., "requires production access", "needs stakeholder approval").

### Edit Tool Usage

Use the Edit tool to update plan checkboxes directly:

```
edit({
  filePath: "thoughts/shared/plans/my-plan.md",
  oldString: "## Phase 2: Core Implementation",
  newString: "## Phase 2: Core Implementation ✓"
})
```

For checkbox updates:
```
edit({
  filePath: "thoughts/shared/plans/my-plan.md",
  oldString: "- [ ] All tests pass",
  newString: "- [x] All tests pass"
})
```

### Partial Completion

If a phase is partially complete (some criteria pass, some fail):
- Do NOT mark phase header complete
- Mark individual passing criteria with `[x]`
- Leave failing criteria as `[ ]`
- Document what remains in validation report

## Anti-Patterns

- **NEVER implement phases yourself** - Always spawn Implement agents via Task tool
- **NEVER write code, tests, or edit source files** - That's the Implement agent's job
- **NEVER run implementation commands** - Only run commands to verify Implement's work
- **Don't skip validation gates** - Every phase must be validated
- **Don't commit to feature branch directly** - Always use plan branches
- **Don't leave worktrees orphaned** - Always cleanup after PR merge
- **Don't continue after BLOCKED verdict** - Wait for resolution
- **Don't assume "manual" means "skip"** - Attempt all verification with available tools
- **Don't mark phase complete if any criteria failed** - Only mark when ALL pass
