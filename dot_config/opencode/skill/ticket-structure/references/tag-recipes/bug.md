<tag-recipe name="bug">

<overview>
A `bug` ticket fixes broken behavior. Something the system was supposed to do correctly is doing it wrong. Light-to-medium depth — Q↔R focuses on reproduction and root cause, D focuses on fix approach, no comprehensive feature-level design.
</overview>

<depth-expectations>
| Phase | Depth |
|---|---|
| Q↔R | 2-5 turns typical |
| D | Fix approach only — no full artifact chain |
| S | Flat section list; numbered Parts only if the bug spans multiple layers |
| P | Standard order; one checkpoint typical |
| I | 100-400 lines typical |
| V | Self-review only; no ticket-reviewer subagent (per spec §10.1) |
</depth-expectations>

<mandatory-sections>
1. **Reproduction Steps** — exact sequence to reproduce the bug
2. **Expected vs Actual** — what should happen vs what does happen
3. **Root Cause Hypothesis** — if known from Q↔R research; otherwise mark "investigation needed"
4. **Fix Approach** — what changes are needed to resolve (WHAT, not HOW)
5. **Acceptance Criteria** — testable: bug no longer reproduces; regression test exists
6. **Out of Scope** — adjacent bugs or refactoring that might seem related but are separate
</mandatory-sections>

<optional-sections>
- **Related Issues** — prior bug reports or symptoms that are the same root cause
- **Severity** — when severity matters for prioritization (paired with secondary tags like `security` if applicable)
- **Workaround** — short-term workaround until the fix lands (rarely needed; usually for hotfix)
- **Risk Areas** — when the fix touches sensitive code paths
</optional-sections>

<ac-patterns>
Bug ACs are **regression-preventing**:

- "Step-by-step reproduction from the Reproduction Steps section no longer produces the bug."
- "A regression test exists that fails before the fix and passes after."
- "Edge cases X, Y, Z are also handled correctly (not just the original reproduction)."
- "Error messages on adjacent failure paths remain unchanged."

The "regression test exists" AC is non-negotiable for bug tickets — without it, the bug can recur silently.
</ac-patterns>

<common-pitfalls>
- **No reproduction steps**: a bug report without reproduction is unfixable; if the user can't provide reproduction, escalate to exploration tag for investigation
- **Symptoms vs root cause**: the user reports a symptom; ticket-grill investigates and may discover the root cause is one layer deeper. The Fix Approach should target ROOT CAUSE, not symptom suppression
- **Scope creep**: fixing the bug surfaces adjacent code smells; resist refactoring during a bug fix. Out of Scope should call this out explicitly
- **Missing edge cases**: the bug may have multiple manifestations; one reproduction is the trigger but others may exist. Q↔R should probe for the full surface
</common-pitfalls>

<q-r-focus-areas>
When grilling a bug:
- Can you reproduce it? What's the exact sequence?
- What did you expect to happen?
- What did happen instead?
- When did this start? (regression vs always-broken)
- Are there workarounds you've been using?
- Have similar bugs been reported? (search thoughts/)

If reproduction is unclear after 2-3 Q↔R turns, recommend switching to exploration tag for an investigation spike.
</q-r-focus-areas>

<length-estimate>
Typical bug ticket: 200-400 lines. Trivial bugs (one-liner regressions): 100-200. Complex bugs spanning multiple subsystems: 400-600.

Beyond 600 lines suggests the bug is actually a feature-shaped fix (architectural change to prevent a class of bugs) — consider re-tagging to feature or infrastructure.
</length-estimate>

<branch-prefix>
Single plan: `fix/{ticket-slug}`
Multi-plan:  `fix/{ticket-slug}-plan-{n}`
</branch-prefix>

</tag-recipe>
