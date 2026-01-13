---
name: pr-review-orchestration
description: |
  Automated PR review cycle for RPIV orchestration. Waits for Gemini reviews,
  assesses feedback, implements fixes, and manages the review loop. Used by
  Planner agent after RPIV opens PRs. This skill is triggered automatically
  by RPIV when entering the PR Review phase.
---

# PR Review Orchestration

## Overview

This skill enables the Planner agent to handle the complete Gemini review cycle for a PR. It provides an automated workflow that:

1. **Waits** for Gemini to post a review (using `await_pr_review` tool)
2. **Assesses** each review thread against actual code (spawns Researcher)
3. **Validates** assessment quality before implementation (spawns Validator)
4. **Implements** approved fixes (spawns Implement)
5. **Responds** to threads and resolves them
6. **Re-reviews** by requesting Gemini to review changes
7. **Loops** until exit condition is met
8. **Escalates** to human for merge decision

## Critical Constraints

### NEVER DO

**NEVER merge PRs**
You are NOT authorized to merge. You MUST escalate to human for merge decisions.
This is non-negotiable. Violation breaks the entire trust model.

**NEVER skip research**
The Researcher MUST spawn sub-agents to read actual code.
Decisions based solely on Gemini's description are FORBIDDEN.

**NEVER trust Gemini blindly**
Gemini lacks project context. All concerns require independent verification.
Your job is to evaluate, not rubber-stamp.

### MUST Follow

- **MUST** write assessment to `thoughts/shared/pr-reviews/{pr}/assessment.md`
- **MUST** spawn Validator after Researcher completes (no skipping the gate)
- **MUST** use `await_pr_review` tool to wait for Gemini (no manual polling loops)
- **MUST** update `thoughts/shared/pr-reviews/{pr}/state.md` after each cycle
- **MUST** escalate to RPIV when ANY exit condition is met:
  - Gemini approves (ready for merge)
  - All items declined/deferred (no code changes made)
  - Timeout waiting for Gemini
  - Context warning received (after completing current cycle)
- **MUST** track iteration count for reporting (no arbitrary limit)

## Workflow Initialization

When entering PR review orchestration, track state:

```
todowrite([
  { id: "prr-init", content: "Initialize PR review state", status: "pending", priority: "high" },
  { id: "prr-wait", content: "Wait for Gemini review", status: "pending", priority: "high" },
  { id: "prr-assess", content: "Assess review threads", status: "pending", priority: "high" },
  { id: "prr-validate", content: "Validate assessment", status: "pending", priority: "high" },
  { id: "prr-implement", content: "Implement approved fixes", status: "pending", priority: "medium" },
  { id: "prr-respond", content: "Respond to threads", status: "pending", priority: "medium" },
  { id: "prr-rereview", content: "Request re-review", status: "pending", priority: "medium" },
])
```

## Phase: Initialize

Set up tracking variables:

- `iteration_count = 0`
- `context_warning_received = false`
- `pr_number` (from RPIV handoff)
- `owner/repo` (from git remote)
- `worktree_path` (from RPIV handoff)
- `branch` (from RPIV handoff)
- `last_action_time = now()` (ISO timestamp)

Create directory for PR review files:
```bash
mkdir -p thoughts/shared/pr-reviews/{pr_number}
```

**If continuing from handoff**: Read state from `thoughts/shared/pr-reviews/{pr}/state.md` to restore iteration count and last action time.

## Phase: Wait for Gemini Review

Call the `await_pr_review` tool and BLOCK until it returns.

```
await_pr_review({
  pr: {pr_number},
  after: "{last_action_time}",
  timeout_minutes: 120
})
```

The tool will:
1. Poll GitHub for Gemini activity (reviews AND issue comments)
2. When first activity detected, start a 3-minute settling window
3. Collect all activity during the window
4. Return everything collected

**On return, YOU must interpret the results:**

### Step 1: Check Tool Status

| Status | Action |
|--------|--------|
| `timeout` | EXIT: Escalate to human with warning |
| `cancelled` | EXIT: Escalate to human |
| `activity_detected` | Continue to Step 2 |

### Step 2: Interpret Collected Data

The tool returns three arrays: `reviews`, `unresolved_threads`, and `issue_comments`.

**Decision tree:**

```
IF unresolved_threads.length > 0:
    -> Continue to ASSESS phase (Gemini has feedback to address)

ELSE IF reviews.length > 0:
    Check the latest review state:
    IF state == "approved":
        -> EXIT: Ready for human merge decision
    ELSE:
        -> EXIT: Ready for human merge decision (reviewed, no threads)

ELSE IF issue_comments.length > 0:
    Read the comment content:
    IF comment says "reviewing" or "will post feedback":
        -> Invoke tool again (Gemini is still processing)
    ELSE IF comment indicates satisfaction ("addressed", "looks good", etc.):
        -> EXIT: Ready for human merge decision
    ELSE:
        -> Invoke tool again (ambiguous, wait for more)

ELSE:
    -> This shouldn't happen with activity_detected status
```

### Key Interpretation Rules

1. **Threads present** = Work to do (always go to ASSESS)
2. **Review only, no threads** = Gemini reviewed but found nothing (exit)
3. **Comment only, no review** = Gemini might be happy OR still processing
   - Read the comment content to decide
   - If unsure, invoke tool again with same timeout
4. **Never skip ASSESS** if there are unresolved threads

**CRITICAL**: Do NOT implement your own polling loop. The tool handles polling and settling.
**CRITICAL**: The tool does NOT interpret Gemini's happiness - YOU must read the comments.

## Phase: Assess Review Comments

Spawn a Researcher agent to independently analyze each unresolved thread.

```
task({
  subagent_type: "researcher",
  description: "PR #{pr_number} review assessment",
  prompt: "<load from references/researcher-prompt.md, substituting variables>"
})
```

**Researcher MUST:**
1. Spawn `codebase-analyzer` for EACH thread to read actual code
2. Understand WHY the code was written this way
3. Evaluate Gemini's concern against reality
4. Recommend: Address | Decline | Defer
5. Write structured assessment to file

**Output**: `thoughts/shared/pr-reviews/{pr}/assessment.md`

## Phase: Validate Assessment

Spawn a Validator agent to review the Researcher's assessment.

```
task({
  subagent_type: "validator",
  description: "PR #{pr_number} assessment validation",
  prompt: "<load from references/validator-prompt.md, substituting variables>"
})
```

**Validator checks:**
- Did Researcher actually verify against code? (evidence required)
- Are Address/Decline/Defer decisions reasonable?
- Are there any obvious errors in judgment?

| Verdict | Action |
|---------|--------|
| APPROVED | Continue to IMPLEMENT phase |
| REJECTED | Return to ASSESS with Validator's feedback |

**Track rejection count. If rejection_count > 3, EXIT and escalate to human.**

## Phase: Implement Fixes

If assessment has items marked Address, spawn Implement agent.

```
task({
  subagent_type: "implement",
  description: "PR #{pr_number} review fixes",
  prompt: "<load from references/implement-prompt.md, substituting variables>"
})
```

**Implement agent:**
1. Read approved items from assessment.md
2. Make minimal changes to address each item
3. Run tests and build
4. Commit with message: "Address PR review feedback: {summary}"
5. Push to PR branch
6. Return commit SHA

**If no Address items**: Skip to RESPOND phase.

**Output**: Commit SHA recorded in `thoughts/shared/pr-reviews/{pr}/changes.md`

## Phase: Respond to Threads

For EACH thread in the assessment, use this skill's justfile recipes.

**Justfile**: `{base_dir}/justfile` (reply, resolve, request-review)

**If Address (and implemented):**
```bash
just -f {base_dir}/justfile reply {owner} {repo} {pr} {comment_id} "**Addressed in commit {SHA}**

{Brief description of change}"
just -f {base_dir}/justfile resolve {thread_id}
```

**If Decline:**
```bash
just -f {base_dir}/justfile reply {owner} {repo} {pr} {comment_id} "**Declined**

{Rationale from assessment - WHY this is by design or incorrect}"
just -f {base_dir}/justfile resolve {thread_id}
```

**If Defer:**

You MUST create a GitHub issue to track the deferred work. Use `gh issue create` directly:

```bash
# Step 1: Create the issue and capture the issue number
gh issue create \
  --title "Type Safety: {brief description of deferred item}" \
  --body "## Deferred from PR #{pr_number}

**Original thread**: {file}:{line}
**Gemini severity**: {severity}

### Issue
{Description of the type safety or other concern}

### Why Deferred
{Rationale - e.g., fix requires cascading changes, exceeds PR scope}

### Proposed Fix
{What needs to be done}

### References
- PR: #{pr_number}
- Thread: {link to comment}" \
  --label "deferred"
```

The command will output the issue URL. Extract the issue number from it.

```bash
# Step 2: Reply to the thread with the issue number
just -f {base_dir}/justfile reply {owner} {repo} {pr} {comment_id} "**Deferred**: Tracked in #{issue_number}

{Brief rationale for deferral}"

# Step 3: Resolve the thread
just -f {base_dir}/justfile resolve {thread_id}
```

**IMPORTANT**: You must create the issue FIRST to get the issue number. Do not reply with "follow-up ticket" or similar vague language - always include the actual issue number.

**CRITICAL**: Always resolve threads after replying. Unresolved threads = incomplete work.

## Phase: Request Re-Review

After all threads are responded to and resolved:

```bash
just -f {base_dir}/justfile request-review {owner} {repo} {pr} "## Review Feedback Summary

@gemini-code-assist All feedback has been addressed.

| Thread | Status | Details |
|--------|--------|---------|
| {path}:{line} | Fixed | Commit {sha} |
| {path}:{line} | Declined | {reason} |
| {path}:{line} | Deferred | Issue #{num} |

Please re-review the changes."
```

**After requesting re-review:**
1. Increment `iteration_count`
2. Update `last_action_time = now()`
3. Update state file (see State File Format below)
4. **Check for context warning**: If you received a context threshold warning during this cycle:
   - Set `context_warning_received = true`
   - EXIT with CONTEXT_HANDOFF report (see below)
5. **MANDATORY: Return to WAIT phase and call `await_pr_review`**

---

## CRITICAL: You MUST Wait for Gemini

**Do NOT check thread counts yourself to determine completion.**

The ONLY way to know if review is complete:
1. Call `await_pr_review` after requesting re-review
2. Interpret Gemini's response (see WAIT phase decision tree)

| ❌ WRONG | ✅ RIGHT |
|----------|----------|
| "I resolved all threads, so I'm done" | "I resolved threads, requested re-review. Now I WAIT for Gemini." |
| Checking `isResolved` status yourself | Using `await_pr_review` to get Gemini's response |
| Exiting because thread count is 0 | Exiting because `await_pr_review` says Gemini approved |

**Why this matters**: Gemini may post NEW threads after you resolve previous ones. Only the `await_pr_review` tool can tell you if Gemini is truly satisfied with the changes.

---

## Context Warning Handling

The context monitor plugin will inject a warning message when context reaches 60%:
> "STOP IMMEDIATELY. Context threshold (60%) reached..."

**When you receive this warning:**
1. **Do NOT stop mid-cycle** - Complete through RE-REVIEW phase
2. After RE-REVIEW, update state file with current progress
3. EXIT with CONTEXT_HANDOFF status (not an error - this is normal)
4. RPIV will spawn a fresh instance to continue

This ensures work is never lost and handoffs happen at clean boundaries.

## State File Format

Update after each cycle: `thoughts/shared/pr-reviews/{pr}/state.md`

```markdown
# PR #{pr_number} Review State

**Last Updated**: {ISO timestamp}
**Iteration**: {count}
**Status**: IN_PROGRESS | WAITING_FOR_GEMINI | COMPLETE | HANDOFF

## Progress
- Threads total: {n}
- Addressed: {n}
- Declined: {n}
- Deferred: {n}

## Last Action
- Type: RE_REVIEW_REQUESTED | WAITING | ASSESSING
- Time: {ISO timestamp}
- After: {timestamp to use for await_pr_review}

## Commits This Session
- `{sha}`: {message}
```

## Exit Conditions

**All exits (except context warning) are triggered by `await_pr_review` results:**

| Condition | Detection via `await_pr_review` | Action |
|-----------|--------------------------------|--------|
| Gemini approves | Returns with 0 `unresolved_threads` and review state is `approved` | Exit -> COMPLETE report |
| Gemini satisfied | Returns with 0 `unresolved_threads` (no new feedback) | Exit -> COMPLETE report |
| All declined/deferred | You declined/deferred all threads, then `await_pr_review` shows no new threads | Exit -> COMPLETE report |
| Timeout | Returns `status: "timeout"` | Exit -> TIMEOUT report |
| Context warning | Received 60% threshold warning (NOT from await_pr_review) | Exit -> CONTEXT_HANDOFF report |
| Validator rejects 3x | `rejection_count > 3` | Exit -> ERROR report |

**Key point**: Even if YOU resolved all threads, you must still call `await_pr_review` to confirm Gemini doesn't post new ones.

## Report Formats

When exiting, return structured report to RPIV based on exit condition:

### COMPLETE Report (Ready for merge / No changes)

```markdown
PR_REVIEW_COMPLETE

PR: #{pr_number}
Status: READY_FOR_MERGE | NO_CHANGES_NEEDED
Iterations: {count}

Summary:
- Threads assessed: {n}
- Addressed: {n}
- Declined: {n}  
- Deferred: {n}
- Commits: {n}

Files:
- Assessment: thoughts/shared/pr-reviews/{pr}/assessment.md
- Changes: thoughts/shared/pr-reviews/{pr}/changes.md
- State: thoughts/shared/pr-reviews/{pr}/state.md
```

### CONTEXT_HANDOFF Report (Context warning received)

**This is not an error** - it's a normal handoff for continuation.

```markdown
PR_REVIEW_HANDOFF

PR: #{pr_number}
Status: CONTEXT_LIMIT_REACHED
Iterations: {count}
Reason: Context threshold (60%) reached after completing cycle {n}

Current State:
- Phase: WAITING_FOR_GEMINI (clean handoff point)
- Last action: RE_REVIEW_REQUESTED at {timestamp}
- After timestamp: {timestamp for next await_pr_review}

Progress So Far:
- Threads assessed: {n}
- Addressed: {n}
- Declined: {n}
- Deferred: {n}

Recommendation: Spawn fresh instance to continue.
State file: thoughts/shared/pr-reviews/{pr}/state.md
```

### TIMEOUT Report

```markdown
PR_REVIEW_TIMEOUT

PR: #{pr_number}
Status: GEMINI_TIMEOUT
Iterations: {count}
Waited: {minutes} minutes for Gemini response

Files:
- State: thoughts/shared/pr-reviews/{pr}/state.md
```

### ERROR Report

```markdown
PR_REVIEW_ERROR

PR: #{pr_number}
Status: VALIDATION_FAILED
Reason: {description}
Iterations: {count}

Files:
- State: thoughts/shared/pr-reviews/{pr}/state.md
```
