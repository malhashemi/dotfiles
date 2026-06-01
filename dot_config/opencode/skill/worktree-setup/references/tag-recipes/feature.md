<tag-recipe name="feature">

<overview>
A `feature` ticket adds a new product capability. User-facing or API-facing behavior that didn't exist before. This is the heaviest of the six primary tags — full Q↔R/D/S/P depth, decision-grade contracts, comprehensive acceptance criteria.
</overview>

<depth-expectations>
| Phase | Depth |
|---|---|
| Q↔R | 4-10 turns typical; complex features may need 10+ |
| D | Full artifact-chain mapping; multiple decision points |
| S | Heavy ticket with numbered Parts when length >600 lines |
| P | Sections-first order with mandatory checkpoints |
| I | 400-1500+ lines typical |
| V | Self-review + ticket-reviewer subagent dispatch (mandatory for feature tag) |
</depth-expectations>

<mandatory-sections>
1. **Problem Statement** — why this feature exists; what user need or business goal it serves
2. **User Stories or Behaviors** — what the user (or system) should be able to do; described behaviorally, not procedurally
3. **Key Interfaces** — interfaces, types, schemas, API endpoints affected (durable identifiers; no file paths in body)
4. **Acceptance Criteria** — testable behaviors; each AC is independently verifiable
5. **Out of Scope** — what this feature does NOT cover; adjacent features that might seem related but are separate
6. **Decision Records** — wiki-links to DRs spawned during ticket-writing (with one-line summaries)
7. **Risk Areas** — where friction is most likely; evidence-bound with research findings
</mandatory-sections>

<optional-sections>
- **Edge Cases** — deletion behavior, error states, permissions, concurrency
- **Migration / Rollout** — when feature touches existing data or rollout strategy matters
- **Performance Considerations** — when performance characteristics are part of the contract
- **Security Considerations** — when security is a primary concern (often paired with secondary tag `security`)
- **Dependencies** — upstream tickets, briefs, or specs this feature depends on
- **Cross-references** — prior thoughts/ artifacts (research, briefs) this feature extends
</optional-sections>

<heavy-ticket-parts-pattern>
When the feature is large (>600 lines estimated), use numbered Parts:

- **Part 1: Context and Decisions** — Problem Statement, Decision Records section, foundational behaviors
- **Part 2: Behavior and Contract** — User Stories, Key Interfaces, Acceptance Criteria, Edge Cases
- **Part 3: Risk and Adjacent** — Risk Areas, Out of Scope, Dependencies, Cross-references
</heavy-ticket-parts-pattern>

<ac-patterns>
Feature acceptance criteria are **user-observable** or **API-observable**:

- "Running `gh issue list --label needs-triage` returns issues that have been through initial classification."
- "POST /api/teams with `{name, description}` creates a team and returns 201 with the team's canonical ID."
- "When a user with no teams loads the dashboard, the team-switcher shows an onboarding prompt to create their first team."
- "A team with status=deleted does not appear in GET /api/teams responses for any user."

Each AC names a TESTABLE behavior — something that can be checked with an automated test or a manual reproduction.
</ac-patterns>

<common-pitfalls>
- **Smuggling tactics**: feature tickets are most prone to "while you're in there, also..." additions that drift toward implementation prescription. Discipline: WHAT, not HOW.
- **Vague AC**: "should work correctly" / "must be performant" creep in when the Q↔R didn't sharpen the behavior boundaries. Force every AC through the "is this testable as written?" check.
- **Insufficient Out of Scope**: feature requests often have implicit assumptions about adjacent features. Surface them in Out of Scope explicitly so the implementer doesn't gold-plate.
- **Single AC**: a real feature has multiple ACs (typical 4-12). One AC usually means the feature wasn't decomposed enough during ticket-grill.
- **Missing DR for vendor / approach choice**: if Q↔R chose between alternatives (e.g., one API design over another), check the three-condition gate — it likely qualifies for a DR.
</common-pitfalls>

<q-r-focus-areas>
When grilling a feature, ensure Q↔R covers:
- What user (or system) does this serve?
- What's the user journey end-to-end?
- What does the system look like AFTER this is built?
- What ALREADY exists in the codebase that this should leverage or replace?
- What are the edge cases (permissions, deletion, concurrency, errors)?
- What does NOT change?
- Are there competitor or domain patterns worth referencing?
</q-r-focus-areas>

<length-estimate>
Typical feature ticket: 600-1200 lines. Small features: 400-600. Large features that should probably decompose downstream: 1200-1500+. If a feature is estimated >1500 lines, flag the implementation-QRDSPIV's P-phase as the decomposition decision point.
</length-estimate>

<branch-prefix>
Single plan: `feat/{ticket-slug}`
Multi-plan:  `feat/{ticket-slug}-plan-{n}`
</branch-prefix>

</tag-recipe>
