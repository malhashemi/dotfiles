# Plan Reconciliation Workflow

Detailed workflow for reconciling implementation with the original plan before merge.

## When This Applies

- PR implements a plan from `thoughts/` directory
- Agent typically knows the plan (user asks agent to read it before PR review)
- If plan location is unknown, ask user

Skip this workflow for quick PRs with no associated plan.

## Base Branch Detection

The base branch is auto-detected from PR metadata:

```bash
# From pr-info output
baseRefName: "main"  # or "master", "dev", etc.
```

Use this for diff comparison—no need to ask user.

## Reconciliation Steps

### 1. Analyze Implementation vs Plan

Compare the actual changes against planned phases:

```bash
# View all changes from base branch
git diff {baseRefName}...HEAD

# Or summarize by file
git diff {baseRefName}...HEAD --stat
```

Review each plan phase and identify:
- What was implemented as planned
- What diverged from the plan (and why)
- What was added that wasn't in the plan
- What was planned but not implemented (if any)

### 2. Correct Plan Details

Update the plan to reflect reality. Focus on:

| Correct | Don't Expand |
|---------|--------------|
| File paths that changed | Adding implementation details not in original |
| Approach that diverged | Increasing verbosity beyond original style |
| Scope adjustments | Adding new sections |
| Phase boundaries | Over-documenting decisions |

The goal is **accuracy**, not **comprehensiveness**. Match the plan's existing level of detail.

### 3. Mark Phases Complete

Update phase status markers in the plan. Common conventions:

```markdown
### Phase 1: Foundation [COMPLETE]
or
### Phase 1: Foundation ✅
or
- [x] Phase 1: Foundation
```

Match the convention already used in the plan.

### 4. User Confirmation

Present summary of changes to plan:

```markdown
## Plan Reconciliation Summary

**Plan**: `thoughts/shared/plans/2025-12-01_feature-x.md`
**PR**: #{pr_number} ({baseRefName} ← {headRefName})

### Changes Made to Plan:
- Corrected file path in Phase 1: `src/old.ts` → `src/new.ts`
- Marked Phase 1 as complete
- Noted scope adjustment: X was deferred to Phase 2

Ready to merge?
```

**CHECKPOINT**: Wait for user approval before proceeding to merge.

## Example

**Before** (plan):
```markdown
### Phase 1: Config Schema [IN PROGRESS]
- Add new config types to `src/config.ts`
- Create validation function
```

**After** (reconciled):
```markdown
### Phase 1: Config Schema [COMPLETE]
- Add new config types to `src/config.ts`
- Create validation function in `src/validation.ts` (separated for clarity)
```

Note: Only the file path was corrected and status updated. No additional detail added.
