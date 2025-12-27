---
description: Review a ticket for issues with severity classification
agent: caster
argument-hint: "[ticket-path]"
---

## Variables

### Dynamic Variables
TICKET_PATH: $ARGUMENTS

## Instructions

Load the ticket review skill and review a ticket.

skill(name="ticket-review")

**If {{TICKET_PATH}} provided**: Review the ticket at that path.

**If no path provided**: Infer from conversation context - look for the ticket being discussed above this command invocation. If ambiguous, ask the user to specify.

Follow the skill's review workflow:
1. Read the full document
2. Analyze for gaps, inconsistencies, ambiguity, and completeness
3. Classify findings by severity (Critical, High, Medium, Low)
4. Present findings with specific before/after proposals
5. Wait for approval before applying any changes
