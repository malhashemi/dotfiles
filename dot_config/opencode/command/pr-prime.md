---
description: Prime PR review context from plan, PR description, and optional research, validation, and tickets
argument-hint: "[plan] [pr-desc] [research] [validation] [tickets]"
---

## Variables

### Dynamic Variables

- ARGUMENTS = $ARGUMENTS
  argument-hint: "[research] [plan] [pr-desc]"

PLAN_FILE: [plan path if provided, otherwise infer from conversation context]
PR_DESC_FILE: [pr-desc path if provided, otherwise infer from conversation context]
RESEARCH_FILE: [research path if provided, otherwise infer from conversation context]
VALIDATION_FILE: [validation path if provided, otherwise infer from conversation context]
TICKETS_FILE: [tickets path if provided, otherwise infer from conversation context]

## Instructions

Read the following files to prime context for PR review:

**Required** (warn if not found):
1. **Plan**: {{PLAN_FILE}}
2. **PR Description**: {{PR_DESC_FILE}}

**Optional** (MUST read if available, skip silently only if not found):
3. **Research**: {{RESEARCH_FILE}}
4. **Validation**: {{VALIDATION_FILE}}
5. **Tickets**: {{TICKETS_FILE}}

If Plan or PR Description cannot be found or inferred, warn about the missing required file(s).

After reading, provide a brief summary of the context: what problem is being solved, the approach taken, and current PR state.
