---
name: ticket-create
description: |
  Guides creation of well-structured tickets (task documents). This skill should be used when 
  the user wants to create a ticket, task, feature request, bug report, or any work item that 
  needs to be tracked and potentially assigned. Provides structure hints without enforcing 
  rigid templates - the final structure adapts to the specific task and domain.
---

# Ticket Create

## Overview

This skill augments Caster's document creation workflow for tickets - task documents that describe work to be done. Tickets can represent features, bugs, improvements, research tasks, or any actionable work item.

## When to Use

- User wants to create a ticket, task, or work item
- User has scattered thoughts about work that needs to be done
- User says things like "I need to track this", "let's create a ticket for...", "this should be a task"
- The `/ticket-create` command is invoked

## Document Type

**Type**: Ticket (task document)

Unlike context packs (reference material), tickets are **actionable** - they describe work to be completed. They typically move through states (draft → active → completed) and may be assigned to someone.

## Ticket Complexity

Tickets vary significantly in scope. Match structure to complexity:

| Complexity | Example | Typical Length | Structure |
|------------|---------|----------------|-----------|
| **Simple** | Bug fix, small task | 50-150 lines | Summary + Requirements + Acceptance Criteria |
| **Medium** | Feature addition | 150-400 lines | Summary + Context + Requirements + Implementation Notes + AC |
| **Large** | System refactor | 400-1500+ lines | Summary + Numbered Parts + Decisions + Questions + AC |

For large tickets, use **numbered Parts** to organize complex content:
- `## Part 1: Overview`
- `## Part 2: Component A`
- `## Part 3: Component B`
- etc.

## Workflow Adaptations

When creating a ticket, adapt Caster's standard workflow:

### Gap Analysis Focus

During gap analysis, specifically look for:

- **What** needs to be done (the actual task)
- **Why** it matters (context, motivation, impact)
- **Scope** boundaries (what's included, what's explicitly excluded)
- **Success criteria** (how to know when it's done)
- **Dependencies** (what must happen first, what this blocks)

### Clarification Questions

Prioritize questions about:

1. Scope and boundaries - what's in, what's out?
2. Success criteria - how will completion be measured?
3. Priority and urgency - how important is this relative to other work?
4. Dependencies - does this block or depend on other work?
5. Assignment - who should work on this?

### Structure Proposal

Propose structure based on the **specific task**, not a fixed template. Common sections include:

| Section | When to Include |
|---------|-----------------|
| Summary | Always - numbered list of key changes/requirements |
| Context/Background | When motivation or history matters |
| Parts (numbered) | For large tickets with multiple components |
| Requirements/Scope | When task has specific deliverables |
| Decisions Made | When documenting choices (table format) |
| Resolved Questions | When key decisions need rationale |
| Acceptance Criteria | When success needs to be measurable (checkboxes) |
| Implementation Notes | For technical tasks with design decisions |
| Open Questions | When decisions are still pending |
| References | Links to relevant code, docs, or other tickets |

**Do NOT enforce all sections** - include only what serves this specific ticket.

## Frontmatter

### Generating Git Context

Before creating frontmatter, run the metadata script to get git context:

```bash
.opencode/scripts/spec_metadata.sh
```

Or use `thoughts metadata` to get current values.

### Complete Frontmatter Structure

```yaml
---
# Git context (from metadata script)
date: 2025-01-15T10:30:00+03:00
researcher: username                # Who created this
git_commit: abc1234
branch: feature/my-feature
repository: project-name

# Document type
kind: ticket
status: draft                       # draft | active | blocked | implemented | verified | abandoned
topic: "Brief Descriptive Title"
tags: [feature, api, refactor]      # Categorization
source: manual                      # manual | linear | github | jira

# Priority and tracking
priority: 2                         # 0-4 (P0=critical, P4=backlog)
schema_version: 1

# References (enables wiki-links)
aliases:
  - ticket-2025-01-15-descriptive-slug

# Optional fields
assignee: alice                     # Who's responsible
due: 2025-02-01                     # YYYY-MM-DD deadline
depends_on:                         # What must complete first
  - "[[other-ticket-alias]]"

# Change tracking (updated automatically on edits)
last_updated: 2025-01-15T10:30:00+03:00
last_updated_by: username
last_updated_note: "Initial creation"
---
```

### Minimal Frontmatter (for simple tickets)

```yaml
---
date: 2025-01-15T10:30:00+03:00
researcher: username
kind: ticket
status: draft
topic: "Fix login button alignment"
tags: [bug, ui]
priority: 3
aliases:
  - ticket-2025-01-15-login-button-fix
---
```

## Save Location

Tickets are saved to the **current project's** thoughts directory:

```
{project}/thoughts/shared/tickets/YYYY-MM-DD_descriptive-slug.md
```

After saving, remind the user to run `thoughts sync` to commit and push changes.

## Alias Convention

Format: `{kind}-{YYYY-MM-DD}-{descriptive-slug}`

Examples:
- `ticket-2025-01-15-user-auth-flow`
- `ticket-2025-01-15-api-rate-limiting`
- `ticket-2025-01-15-dashboard-redesign`

## Acceptance Criteria Format

Use checkbox format for testable criteria:

```markdown
## Acceptance Criteria

### Category 1

- [ ] Specific measurable criterion
- [ ] Another criterion with expected behavior

### Category 2

- [ ] Third criterion
```

Group related criteria under subheadings for large tickets.

## Quality Checklist

Before finalizing, verify:

- [ ] Summary clearly states what needs to be done
- [ ] Scope is defined (or explicitly open-ended)
- [ ] Success criteria exist (even if informal)
- [ ] Alias follows convention
- [ ] Frontmatter has appropriate fields for this ticket
- [ ] Structure matches ticket complexity

## Remember

Tickets are living documents. Start lean - it's better to have a clear, focused ticket than a comprehensive but bloated one. The ticket can be updated as understanding evolves. For large refactors, expect multiple review rounds to refine the specification.
