---
name: plan-review
description: |
  Catch oversized phases BEFORE implementation begins! This skill reviews plans for sizing, 
  dependencies, and completeness - flagging phases that need decomposition before a single 
  line of code is written. Load this when validating plans pre-implementation.
---

# Plan Review

## Overview

Review implementation plans before execution to catch sizing issues, dependency problems, and 
gaps that would cause implementation failures. This is a pre-flight check that prevents wasted
effort.

## When to Use

- After a Planner creates an implementation plan
- Before handing off a plan to implementation
- When RPIV requests plan validation before proceeding
- When user asks to review/validate a plan

## Review Checklist

### 1. Phase Sizing Assessment

For each phase, evaluate:

| Factor | Acceptable | Concerning | Flag for Decomposition |
|--------|------------|------------|------------------------|
| File changes | 1-3 files | 4-6 files | 7+ files |
| New functions/classes | 1-5 | 6-10 | 10+ |
| Test additions | 1-10 tests | 11-20 tests | 20+ tests |
| Estimated context | <30% | 30-40% | >40% |

**Context estimation heuristic**:
- Each file read: ~2-5% context (depending on size)
- Each code generation: ~5-10% context
- Each test run + analysis: ~3-5% context

### 2. Dependency Analysis

For each phase, verify:

- [ ] Phases are correctly ordered (no forward dependencies)
- [ ] Each phase builds on previous phases' outputs
- [ ] No circular dependencies
- [ ] Optional/parallel phases are clearly marked

### 3. Completeness Check

For each phase, verify it includes:

- [ ] Clear description of what to implement
- [ ] Specific files to create/modify
- [ ] Success criteria (automated and manual separated)
- [ ] Any code snippets or patterns to follow

### 4. Gap Analysis

Identify missing elements:

- Are there phases that should exist but don't?
- Are there implicit steps that should be explicit?
- Are error cases and edge cases addressed?
- Is there a testing strategy for each phase?

## Review Process

### Step 1: Read Full Plan

Read the entire plan without making judgments. Understand:
- What is being built
- Why it's structured this way
- What the end state looks like

### Step 2: Phase-by-Phase Assessment

For each phase, create an assessment:

```markdown
### Phase N: [Title]

**Sizing**: ✓ Acceptable / ⚠️ Borderline / ✗ Too Large
- Estimated files: X
- Estimated context: Y%

**Dependencies**: ✓ Clear / ⚠️ Implicit / ✗ Circular

**Completeness**: ✓ Complete / ⚠️ Missing details / ✗ Insufficient

**Notes**: [Any specific concerns or suggestions]
```

### Step 3: Synthesize Verdict

Based on all assessments:

**APPROVED** - Plan is ready for implementation
- All phases are appropriately sized
- Dependencies are clear and logical
- Each phase has sufficient detail

**NEEDS DECOMPOSITION** - Specific phases must be broken down
- List which phases need decomposition
- Explain why (too large, too complex, etc.)
- Suggest how to split if obvious

**NEEDS REVISION** - Plan has structural issues
- List what needs to be fixed
- Dependencies need reordering
- Gaps need to be addressed

## Output Template

```markdown
# Plan Review: [Plan Name]

## Overview
[1-2 sentence summary of what the plan implements]

## Phase Assessments

### Phase 1: [Title]
**Sizing**: ✓ / ⚠️ / ✗
**Dependencies**: ✓ / ⚠️ / ✗  
**Completeness**: ✓ / ⚠️ / ✗
**Notes**: ...

[Repeat for each phase]

## Dependency Graph
```
Phase 1 → Phase 2 → Phase 3
              ↘ Phase 4 (parallel)
```

## Issues Found

### Must Fix Before Implementation
- [Critical issue 1]
- [Critical issue 2]

### Recommendations (Optional)
- [Suggestion 1]
- [Suggestion 2]

## Verdict

**[APPROVED / NEEDS DECOMPOSITION / NEEDS REVISION]**

[Explanation of verdict with specific action items if not approved]
```

## Integration with RPIV

When operating within RPIV:
1. Receive plan from Planner via RPIV orchestration
2. Perform review using this skill
3. Return verdict to RPIV
4. If NEEDS DECOMPOSITION: RPIV triggers Planner to revise specific phases
5. If APPROVED: RPIV proceeds to implementation orchestration
