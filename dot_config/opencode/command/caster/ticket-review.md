---
description: Review a ticket for issues with severity classification
agent: caster
argument-hint: "[path, filename, or query]"
---

## Variables

### Dynamic Variables
USER_INPUT: $ARGUMENTS

## Instructions

Load the ticket review skill and review a ticket.

skill(name="ticket-review")

**Interpret {{USER_INPUT}}**:

1. **Full path** (contains `/` or ends with `.md`): Read the ticket at that path directly.

2. **Filename only** (e.g., `backlog-system-refactor` or `2025-12-26_backlog-system-refactor.md`): Search for it in `thoughts/shared/tickets/` directory.

3. **Search query** (descriptive text like "the backlog ticket" or "refactor ticket"): Search `thoughts/shared/tickets/` for tickets matching the description by filename or content.

4. **No input provided**: Infer from conversation context - look for the ticket being discussed above this command invocation. If ambiguous, list available tickets and ask the user to specify.

Follow the skill's review workflow:
1. Read the full document
2. Analyze for gaps, inconsistencies, ambiguity, and completeness
3. Classify findings by severity (Critical, High, Medium, Low)
4. Present findings with specific before/after proposals
5. Wait for approval before applying any changes
