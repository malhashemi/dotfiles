---
description: Prime PR review context from research, plan, and PR description files
argument-hint: "[research] [plan] [pr-desc]"
---

## Variables

### Dynamic Variables

- ARGUMENTS = $ARGUMENTS
  argument-hint: "[research] [plan] [pr-desc]"

RESEARCH_FILE: [research path if provided, otherwise infer from conversation context]
PLAN_FILE: [plan path if provided, otherwise infer from conversation context]
PR_DESC_FILE: [pr-desc path if provided, otherwise infer from conversation context]

## Instructions

Read the following files to prime context for PR review:

1. **Research**: {{RESEARCH_FILE}}
2. **Plan**: {{PLAN_FILE}}
3. **PR Description**: {{PR_DESC_FILE}}

If any files cannot be found or inferred, note which ones are missing.

After reading, provide a brief summary of the context: what problem is being solved, the approach taken, and current PR state.
