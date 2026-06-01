---
name: decision-record-format
description: "Format and gating rules for Decision Records (DRs) — the immutable audit-grade artifacts that capture hard-to-reverse decisions made during ticket-writing. Use when deciding WHETHER to write a DR (three-condition gate) and HOW to write one (minimal one-paragraph template, optional sections, schema-native frontmatter). Cross-agent: written by ticketsmith during ticket-grill or ticket-design; read by any agent that needs to understand why the system is shaped a certain way."
---

# Decision Record (DR) Format

## Overview

A Decision Record (DR) is an immutable, audit-grade artifact that captures a hard-to-reverse decision and the reasoning behind it. DRs live alongside tickets at `{shared_folder}/decisions/decision-YYYY-MM-DD-{slug}.md` and are auto-numbered `DR-NNN`.

DRs are the structural members of the team's decision history. Acceptance criteria, design summaries, and tactical plans are finish work. DRs carry the WHY.

This skill defines:

- **The three-condition gate** that determines whether a DR is warranted
- **The minimal format** for the DR body (one paragraph minimum)
- **Optional sections** that can be added when they earn their place
- **Frontmatter requirements** (schema-native; populated by `scaffold-decision-record.py`)

## The Three-Condition Gate

A DR is written **only when all three conditions are true**:

1. **Hard to reverse** — meaningful cost to change the decision later. If the decision is easy to reverse, skip the DR; future engineers will just reverse it.
2. **Surprising without context** — a future reader will look at the code or the system and wonder "why on earth did they do it this way?". If the decision is the obvious path, nobody will wonder.
3. **The result of a real trade-off** — there were genuine alternatives and one was chosen for specific reasons. If there was no real alternative, there is nothing to record beyond "we did the obvious thing."

**If any of the three is missing, do not write a DR.** Capture the resolution in the Q&A log or the ticket body, but reserve DRs for the load-bearing decisions only. Over-recording dilutes the signal.

### What Qualifies

The qualifying categories (from mattpocock ADR-FORMAT, adapted for the ticketsmith harness where DRs cover product/scope/vendor/operational decisions, not strictly architecture):

- **Architectural shape.** "We're using event sourcing for the order write-model and projecting into Postgres for reads."
- **Integration patterns between contexts.** "Ordering and Billing communicate via domain events, not synchronous HTTP."
- **Technology choices that carry lock-in.** Database, message bus, auth provider, deployment target. Not every library — just the ones that would take a quarter to swap out.
- **Boundary and scope decisions.** "Customer data is owned by the Customer context; other contexts reference it by ID only." The explicit no-s are as valuable as the yes-s.
- **Deliberate deviations from the obvious path.** "We're using manual SQL instead of an ORM because X." Anything where a reasonable reader would assume the opposite.
- **Constraints not visible in the code.** "We can't use AWS because of compliance requirements." "Response times must be under 200ms because of the partner API contract."
- **Rejected alternatives when the rejection is non-obvious.** If GraphQL was considered and REST was picked for subtle reasons, record it — otherwise someone will suggest GraphQL again in six months.
- **Product decisions with real trade-offs.** "We chose vendor A over vendor B because B's SLA didn't cover our peak traffic window — at the cost of higher per-call price."
- **Operational decisions that shape behavior.** "We retain audit logs for 7 years per compliance, not the 90 days the platform suggests."

### What Does NOT Qualify

- A choice between two functionally identical libraries with no real trade-off.
- A naming convention that can be renamed with a single PR.
- An implementation detail that does not surface in the system's behavior.
- A decision the ticket itself can fully capture (e.g., "Part 3 will use the existing pagination middleware") — that is a tactical note, not a DR.

## Minimal Template

The minimum DR is one paragraph: context, decision, why. Most DRs should fit on a single screen.

```md
# DR-NNN: {Short title of the decision}

**Parent**: [[ticket-YYYY-MM-DD-slug]]

## Context

{1–3 sentences describing the situation that forced the decision. What constraint surfaced? What alternatives were on the table?}

## Decision

{One sentence stating what was decided.}

## Why

{One sentence stating the rationale — the specific reasons this option won over the rejected alternatives.}
```

That's the entire required body. The value is in recording **that** a decision was made and **why** — not in filling out sections.

## Optional Sections

Only include these when they add genuine value. Most DRs will not need them.

### Considered Options

Add when the rejected alternatives are worth remembering — typically because someone might propose them again later.

```md
## Considered Options

- **Option A: Shared tables with team_id.** Simple migration, works with current ORM. Application-enforced isolation. **Chosen.**
- **Option B: PostgreSQL RLS.** Database-enforced isolation. Sequelize doesn't natively support RLS; requires fragile workarounds.
- **Option C: Schema-per-team.** Strongest isolation. Impractical with Sequelize connection pooling at any scale beyond ~50 teams.
```

### Consequences

Add when non-obvious downstream effects need to be called out. The goal is to surface effects that future readers will not infer from the decision itself.

```md
## Consequences

- Application code must enforce team boundaries on every query. Bug here = data leak between teams.
- Migration path to RLS later is documented but adds latency to that future migration.
- Adds a `teamScope` middleware to the request chain; tested at the auth layer.
```

### Status Frontmatter Note

If a DR is later superseded, the new DR adds `supersedes: [[DR-NNN]]` to its frontmatter. The old DR is NOT edited — its `status: accepted` stands, the supersession is recorded in the newer DR's frontmatter and (optionally) in a one-line postscript on the old DR. This preserves the immutability.

## Frontmatter Requirements

DRs use schema-native frontmatter. The scaffold script `scaffold-decision-record.py` populates all required fields automatically from `thoughts metadata` plus the caller's args. Required fields:

| Field | Value |
|---|---|
| `kind` | `decision` |
| `status` | `accepted` (immutable; not `draft` or `active`) |
| `aliases` | `[decision-YYYY-MM-DD-slug, DR-NNN]` (first alias canonical) |
| `parent` | `[[ticket-YYYY-MM-DD-slug]]` (wiki-link to spawning ticket) |
| `owner` + `researcher` | `thoughts metadata` → owner |
| `date`, `git_commit`, `branch`, `repository` | `thoughts metadata` |
| `last_updated`, `last_updated_by`, `last_updated_note` | populated; updated only on supersession |
| `topic` | The DR's one-line title |
| `tags` | `[decision]` plus any qualifying secondary tags |
| `schema_version` | `1` |

## Numbering

DR numbering is global per shared folder. The `scaffold-decision-record.py` script maintains a manifest at `{shared_folder}/decisions/MANIFEST.yaml`:

```yaml
next_dr: 4
decisions:
  - id: DR-001
    title: Use shared tables for team scoping
    slug: shared-tables-team-scoping
    canonical_alias: decision-2026-05-17-shared-tables-team-scoping
    parent_ticket: ticket-2026-05-17-team-workspaces
    created: '2026-05-17T11:27:19+03:00'
  ...
```

Always invoke the script — never hand-author the manifest or skip numbers.

## Immutability

A DR's `status: accepted` is permanent. The DR file is **not edited** after creation except to:

- Add an optional `supersession` postscript (one line) linking to the newer DR that replaces it
- Add the `supersedes:` frontmatter field on the **newer** DR pointing at the older one

If the decision needs to change, write a new DR that supersedes the old one. The old DR stays as historical evidence.

## Writing Style

- **Direct.** No hedging. "We chose X because Y." Not "we have decided to potentially adopt X under certain considerations."
- **Specific.** Name the alternatives. "Not Y because Y has constraint Z" is useful. "We picked the best option" is not.
- **Evidence-bound.** When research informed the decision, link to the research doc in the body. The DR can be short because it references the deeper evidence.
- **Tense.** Past tense for "Decision" and "Context" (the decision was made; the situation existed). Present tense for "Consequences" (the effect is ongoing).

## When to Offer a DR During Grilling

During Q↔R, the agent surfaces a DR opportunity to the user only when the three-condition gate is clearly met. Suggested phrasing:

> "This looks like a hard-to-reverse decision: chose X over Y for reasons A and B. Worth recording as a DR so future readers don't undo it without seeing the trade-off?"

The user confirms or declines. If declined, the resolution is captured in the Q&A log only. If accepted, invoke `scaffold-decision-record.py` immediately.

The DR is written **inline during the grilling session**, not batched at the end. Tickets that spawn DRs link them in the ticket frontmatter `children:` array.
