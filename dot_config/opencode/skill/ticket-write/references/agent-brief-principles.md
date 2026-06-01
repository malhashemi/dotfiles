# AGENT-BRIEF Principles

This reference is loaded by ticket-write's section-drafting step. It captures the durability discipline that makes a ticket survive months of dormancy without context bleed. Adapted from mattpocock's AGENT-BRIEF format and the ticket-writing workflow spec §2.

The finished ticket is consumed by an autonomous implementation agent running its own downstream QRDSPIV. The ticket is therefore an AGENT-BRIEF-discipline artifact: durable, behavioral, decision-grade, self-sufficient.

## Principle 1: Durability over precision

The ticket may sit in `ready` status for days or weeks. The codebase will change in the meantime. Write the ticket so it stays useful even as files are renamed, moved, or refactored.

**Do**:
- Describe interfaces, types, and behavioral contracts
- Name specific types, function signatures, or config shapes the agent should look for or modify
- Use durable identifiers: capability names ("team workspace"), entity names ("Membership"), behavioral descriptors ("invitation accept flow")

**Don't**:
- Reference file paths in section bodies — they go stale
- Reference line numbers
- Assume the current implementation structure will remain the same

**Exception**: In Risk Areas / Evidence sections, citing specific file paths (e.g., "the auth middleware in src/middleware/auth.ts:42 is referenced by 38 route handlers") IS allowed because those citations are evidence-bound to research findings, not prescriptions for where to make changes.

## Principle 2: Behavioral, not procedural

Describe **what** the system should do, not **how** to implement it. The implementation agent will explore the codebase fresh and make its own implementation decisions.

**Good**:
- "The `SkillConfig` type should accept an optional `schedule` field of type `CronExpression`"
- "When a user runs the team-switcher with no teams, they should see an onboarding prompt to create their first team"
- "The /api/teams/:teamId endpoint should return 403 when the requester is not a member of the team"

**Bad**:
- "Open src/types/skill.ts and add a schedule field on line 42"
- "Add a switch statement in the main handler function"
- "Modify the auth middleware to check team membership"

The "Bad" forms prescribe HOW; the "Good" forms describe WHAT. Implementation agents need WHAT; they figure out HOW from current codebase state.

## Principle 3: Complete acceptance criteria

The implementation agent (and the downstream verification process) needs to know when the work is done. Every ticket must have concrete, testable acceptance criteria. Each criterion is independently verifiable.

**Good**:
- "Running `gh issue list --label needs-triage` returns issues that have been through initial classification"
- "POST /api/teams with a valid body creates a team and returns 201 with the team's canonical ID"
- "DELETE /api/teams/:teamId on a team where the requester is not the owner returns 403"

**Bad**:
- "Triage should work correctly"
- "Team APIs should be implemented"
- "The auth should be secure"

Acceptance criteria are the ticket's contract. Vague AC = vague contract = ambiguous implementation = verify-phase findings.

## Principle 4: Explicit scope boundaries

State what is OUT OF SCOPE. This prevents the implementation agent from gold-plating or making assumptions about adjacent features.

Examples of useful out-of-scope statements:
- "Adjacent feature X that might seem related but is separate"
- "Migration of existing data (handled in a follow-up ticket)"
- "Multi-region replication (deferred until cross-region demand is validated)"
- "UI changes (this ticket is API-only)"

The "Out of Scope" section is as load-bearing as the "Behaviors" section. Implementation agents read it to know where to STOP.

## Principle 5: Self-sufficient

The ticket must contain ALL the context the implementation agent needs. The implementation-QRDSPIV's Q↔R may dispatch its own research subagents, but the ticket should not require the agent to re-derive the WHAT-and-WHY from scratch.

**Self-sufficient elements**:
- Problem statement (why this work exists)
- Linked DRs (load-bearing decisions made during ticket-writing)
- Scope boundaries (what's in, what's out)
- Acceptance criteria (testable outcomes)
- Risk areas with evidence (so the implementer knows where to focus attention)
- Cross-references to prior work (briefs, specs, prior tickets) when relevant

**What the ticket does NOT contain** (per spec §2.2):
- File paths in section bodies (Risk Areas exception aside)
- Vertical slices or implementation steps
- Per-phase effort estimates
- Test code
- Helper types or internal mechanics
- Commit strategy

## Principle 6: Decisions belong in the ticket; tactics belong in the plan

The line between ticket-content and plan-content (where "plan" means the implementation-QRDSPIV's P-phase plan, not THIS ticket-plan skill) is sharp:

| Ticket carries | Ticket does NOT carry |
|---|---|
| Problem statement, motivation | File paths |
| Behavioral definition | Vertical slices |
| Decision-grade contracts (interfaces, schemas) | Helper types, internal mechanics |
| Explicit out-of-scope | Commit strategy |
| Acceptance criteria (testable behaviors) | Test code |
| Codebase grounding facts (cited as evidence) | File-by-file change lists |
| Pointers to DRs and sub-tickets | Per-phase effort estimates |

When tempted to add an "implementation hint" to a ticket, that hint belongs in the plan. The ticket draws the line. The plan crosses it.

## Principle 7: Read against the Design Summary

Every section of the ticket should be CONSISTENT with the Design Summary section written by ticket-design. If the AC section's behaviors don't match the Behaviors section earlier in the same ticket, that's a Critical drift. If the Out of Scope section contradicts a Locked DR's decision, that's a Critical drift.

ticket-verify catches these drift cases as Critical findings. But the discipline starts at write-time: every section is drafted with the Design Summary open in working memory.

## Section-by-section quality checklist

When drafting each section, the agent should be able to answer YES to:

- [ ] Is this section's content WITHIN this section's stated scope (per Structure Outline)?
- [ ] Does this section reference durable identifiers, not file paths or line numbers?
- [ ] Does this section describe behavior (what), not implementation (how)?
- [ ] If this section has testable claims, are they actually testable as written?
- [ ] If this section references a DR or prior ticket, is the reference a working wiki-link?
- [ ] Is this section consistent with the Design Summary's promises?

A NO on any of these triggers a re-draft of the section before moving on.
