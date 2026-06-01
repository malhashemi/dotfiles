# Severity Ladder (codesmith V-phase)

Five tiers. Every finding gets exactly ONE severity classification. Use the highest applicable tier — do not undersell.

## Critical — implementation cannot ship in this state

Foundational defects that make the implementation unsafe to merge.

Examples:
- Test that should pass is failing
- Fitness function (linter, scanner, type check, dependency manifest check) reports a violation
- Security vulnerability with realistic exploitation path
- Code path that violates a documented invariant or ADR
- Data-loss risk (silent overwrites, missing rollback)
- Schema migration without rollback plan
- Plan-adherence: claimed step is not implemented

## High — implementation cannot ship until addressed; path is clear

Significant gaps where the fix is well-defined.

Examples:
- Logic error with realistic-but-not-yet-tested scenario
- Missing test for a slice's primary behavior
- Pattern violation (uses a forbidden abstraction, ignores established convention)
- Test that tests implementation shape rather than behavior
- Code quality: deeply nested function that should be extracted (and is in scope per the plan)
- Sizing: plan slice is genuinely too large (revealed mid-implementation)
- Architecture: code crosses a module boundary that ADR forbids

## Medium — can ship but is degraded

Quality issues that don't block but reduce future maintainability. **Medium findings BLOCK unless explicitly waived by user via Question tool.**

Examples:
- Performance: O(n²) on an unbounded input where O(n) is achievable with reasonable effort
- Documentation: CONTEXT.md touched but not updated for a new domain term
- Operational: new code path lacks observability hook (log, metric, trace)
- Test quality: integration test where a unit would suffice (or vice versa)
- Naming: function/variable name diverges from project glossary

## Low — polish items

Suggestions that improve readability without affecting behavior or maintainability much. Non-blocking.

Examples:
- Formatting inconsistency (the linter didn't catch but a human notices)
- Comment that could be clearer
- Repeated logic that could be extracted (but isn't currently in the plan's scope)
- Variable name that could be more descriptive

## Suggestion — improvements outside the implementation's scope

Observations that don't affect this implementation but are worth recording for future work. Non-blocking. Often paired with `scope: codebase-wide` for findings that exceed this implementation's bounds.

Examples:
- Codebase-wide pattern that should be applied consistently (signal to future codebase-review workflow)
- Adjacent module that has the same problem the touched code just fixed
- Refactoring opportunity in code the implementation passed through but did not modify

## Verdict mapping

| Severity present | Verdict |
|---|---|
| Critical | BLOCKED |
| High | BLOCKED |
| Medium | BLOCKED unless explicitly waived by user |
| Low only | PROCEED |
| Suggestion only | PROCEED |

No 'PROCEED_WITH_NOTES'. No 'deferred to later'.

## Calibration

- Be direct. Polite hedging dilutes the severity signal.
- Be specific. Cite file:line. Name the invariant, the test, the pattern.
- One severity per finding. If a finding spans multiple severities, split it.
- Empty severity buckets are fine. A clean gate should pass with few or zero findings.
