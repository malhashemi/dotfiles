# Ticket Severity Ladder

This reference defines the four-level severity classification used by both ticket-verify (self-review during V-phase) AND the ticket-reviewer subagent (fresh-context review). The two audiences need this self-contained, so the ladder is duplicated in ticket-reviewer/instructions.md AND here. Treat the two copies as one specification; if they drift, ticket-verify wins (it's the authoring side).

Every finding gets exactly ONE severity. Do not undersell a foundational issue as Medium because the language is polite. Use the highest applicable level.

## Critical — ticket cannot ship in this state

Foundational defects that make the ticket unsafe to act on. Implementation cannot proceed without resolution.

**Examples**:
- **Foundational contradiction**: ticket body asserts X; research file asserts not-X. The contradiction is unresolved.
- **Decision not captured**: ticket body relies on a hard-to-reverse decision but no DR is linked and no inline rationale is captured. Future engineers cannot reconstruct why.
- **Missing required AC for the primary tag**: feature tickets without observable acceptance criteria; infrastructure tickets without rollback criteria; exploration tickets without explicit research questions and decision points.
- **Scope boundary undefined**: ticket does not state what it does NOT cover. Risk of unbounded interpretation during implementation.
- **Frontmatter schema violation**: invalid status, missing `parent` on a sibling, broken `children` references, custom non-schema fields.
- **Drift from a locked DR**: the ticket body proposes an approach that contradicts a DR linked in its children array.
- **Drift from Design Summary**: the ticket sections promise behaviors not in the Design Summary, OR omit behaviors the Design Summary promised.
- **AGENT-BRIEF principle violation that compromises durability**: the ticket reads as procedural ("open file X, modify line Y") rather than behavioral; future implementation agent cannot work from it without re-deriving WHAT-and-WHY.

## High — ticket cannot ship until addressed but path is clear

Significant gaps where the fix is well-defined.

**Examples**:
- **Implementation smuggling**: ticket body contains tactics ("use Redis", "implement as middleware") that belong in the plan, not the decision artifact. Decisions belong; tactics do not.
- **Vague acceptance criteria**: "should work correctly" / "must be performant" with no measurable bar.
- **Missing context for dormancy**: ticket assumes shared context (recent discussion, in-flight decisions, current team mental model) that won't survive 3 months without explanation.
- **Q&A log → ticket drift**: the Q&A log shows a question was answered one way but the ticket reflects a different answer.
- **Section under/over deviation**: a section came in 50%+ under estimated length (may be missing content) or 50%+ over (may have scope creep that belongs elsewhere).
- **Force-exit at readiness gate**: ticket-grill's readiness gate was force-exited (less than 5/5 criteria met). The bundle is technically usable but the gaps need surfacing.
- **Foundational reversal strike >0 on entry**: the ticket-design strike counter was non-zero. last_updated_note records the count. Review for accumulated incoherence even if the user pushed past.

## Medium — ticket can ship but is degraded

Quality issues that don't block but reduce future maintainability.

**Examples**:
- **Unfocused scope statement**: scope is bounded but the boundary statement is buried in prose instead of being explicit.
- **Stale assumption**: ticket references a state that may have shifted (e.g., "now that Service X uses gRPC" — was that always true?).
- **Missing depends_on links**: ticket clearly blocks on prerequisite work but `depends_on` array is empty.
- **Tag misalignment**: primary tag is `feature` but the work pattern reads more like `infrastructure` (or vice versa). Surface for tag review.
- **Risk Area citation drift**: a Risk Area cites a file path, but the research file's findings reference a different (newer, more accurate) path.
- **Out-of-Scope thinness**: out-of-scope section exists but only has 1-2 items; the implementation agent may gold-plate adjacent features.
- **Dangling wiki-link**: a `[[X]]` / `[[X|alias]]` whose target `X` (the token before any `|`) is not a real filename stem — a broken reference, not mere style. Escalate to **Critical** when the broken link is a frontmatter `parent`/`children`/DR reference (see Critical → "broken `children` references").

## Low — polish items

Suggestions that improve readability without affecting decision durability.

**Examples**:
- **Wikilink format inconsistency**: some links use `[[file]]`, others use `[[file|alias]]`. Recommend consistent `[[file-stem|alias]]` form.
- **Section ordering**: a section reads better in a different position.
- **Repeated content**: same point made twice in adjacent sections.
- **Heading levels off**: a subsection uses level-2 instead of level-3.
- **Tone inconsistency**: one section uses past tense, another uses present, without clear reason.

## Finding output format

Every finding produced by either self-review or subagent review follows this shape:

```md
#### {{severity_initial}}-{{N}}: {{one-line title}}

- **Location**: {{file}}:{{section or line range}}
- **Finding**: {{2-3 sentences describing the defect}}
- **Fix recommendation**: {{concrete action — what to add, change, or remove}}
- **(Medium+ only) Impact**: {{one sentence on what happens if not fixed}}
```

Where `severity_initial` = C for Critical, H for High, M for Medium, L for Low.

The finding report concludes with a Verdict line:
- **BLOCK** — at least one Critical finding present. Ticket cannot transition draft → ready.
- **CONDITIONAL** — High findings present, no Criticals. Ticket can transition ONLY after High findings are resolved or explicitly waived by the user.
- **PASS** — no Critical or High findings. Ticket can transition. Medium and Low are recommendations for future polish.

## Resolution discipline

Per spec §10.2, findings are resolved in three ways:

1. **Self-evident fixes** (e.g., AC missing a verb, wikilink format inconsistency): apply directly via Edit. No user consultation needed.

2. **Ambiguous fixes** (decision implications, design alternatives, anything where the "right" fix is debatable): use the Question tool per finding. The user approves or specifies the fix.

3. **Structural findings** (e.g., AC isn't testable because a behavior was never grilled): loop back to the relevant earlier phase. Examples:
   - "Foundational contradiction between body and research file" → loop to ticket-grill (re-grill to resolve)
   - "Drift from Design Summary" → loop to ticket-design (re-align)
   - "Required section missing" → loop to ticket-structure or ticket-write
   - "Force-exit at readiness gate" → loop to ticket-grill (close the gap)

No "mini-QRDSPIV per finding" — that would reinvent the loop mechanism QRDSPIV already provides. The loop-back uses the existing skill flow.

Loop-backs from V-phase do NOT increment ticket-design's strike counter — they're verify-driven, not user-driven reversals.

## Severity calibration notes

- Be direct. Polite hedging dilutes the severity signal. If something is Critical, call it Critical.
- Be specific. "The acceptance criteria are weak" is unhelpful. "AC #2 says 'works correctly' with no measurable threshold; recommend defining the threshold in terms of response time, error rate, or observable behavior" is useful.
- Be evidence-bound. Cite file:section or file:line for every finding. The author needs to find the issue without re-reading the entire bundle.
- One severity per finding. If a finding spans multiple severities, split it.
- Do not pad. Empty severity buckets are FINE. A clean ticket should pass with few or zero findings.
