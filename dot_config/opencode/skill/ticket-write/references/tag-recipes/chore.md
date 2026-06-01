<tag-recipe name="chore">

<overview>
A `chore` ticket is a small mechanical task. Update a README, rename a field everywhere, bump a dependency, clean up a deprecated comment. Minimal ceremony — the work is well-defined, the scope is narrow, no real decisions to record.
</overview>

<depth-expectations>
| Phase | Depth |
|---|---|
| Q↔R | 1-2 turns; usually just confirming scope |
| D | Trivial — the task is its own description |
| S | Minimal flat section list |
| P | Trivial — do the thing |
| I | 80-200 lines typical |
| V | Self-review only |
</depth-expectations>

<mandatory-sections>
1. **What** — the specific change being made (be precise)
2. **Why** — the reason for the change (even chores have a reason; "stale docs", "dependency upgrade", "consistent naming")
3. **Acceptance Criteria** — testable: change is applied; no regressions
</mandatory-sections>

<optional-sections>
- **Scope** — when the chore touches more than the obvious surface (e.g., renaming a field requires updating every reference)
- **Out of Scope** — adjacent improvements that might seem related but are separate
- **Verification Steps** — when verification is non-trivial (rarely; usually verification is obvious from the change)
</optional-sections>

<ac-patterns>
Chore ACs are **change-confirmation-focused**:

- "Field name X is renamed to Y in all source files (verified via grep)."
- "Dependency Z is upgraded from 1.2 to 2.0 with no test regressions."
- "README section on installation no longer references the deprecated bootstrap script."

Chore ACs are SHORT and SPECIFIC. If a chore needs more than 3-4 ACs, it might actually be a feature-tier task in disguise.
</ac-patterns>

<common-pitfalls>
- **Chore creep**: a "rename field" chore turns into "and also clean up the surrounding code, and add tests, and..." Discipline: chore = the one specific thing. Improvements are separate tickets.
- **No-why chores**: "update the docs" without explaining why misses the point. Even small chores have a reason — capture it in Why so future readers know the change wasn't arbitrary.
- **Misuse for substantial work**: a "small refactor" that touches 30 files is NOT a chore. Use the appropriate tag (likely feature or infrastructure depending on the nature).
- **Misuse for risky changes**: a dependency upgrade that could break tests is NOT a chore (it has risk). Bump it to bug or feature so the verify phase gets proper attention.
</common-pitfalls>

<q-r-focus-areas>
When grilling a chore (which is brief):
- What specifically is being changed?
- Why does it need to happen?
- What's the testable outcome?
- Is there anything adjacent we should NOT touch?

If Q↔R takes more than 1-2 rounds for a chore, the work probably isn't actually a chore — re-tag.
</q-r-focus-areas>

<length-estimate>
Typical chore ticket: 80-200 lines. Trivial chores (one-line change, doc tweak): 50-100. Larger chores that touch many files mechanically: 200-300.

Beyond 300 lines suggests the work is more than mechanical — consider re-tagging to bug, feature, or infrastructure.
</length-estimate>

<when-to-not-use>
The chore tag is for genuinely mechanical, well-defined tasks. It is NOT for:
- Refactoring (use feature or infrastructure)
- Bug fixes (use bug)
- New capability (use feature)
- Investigation (use exploration)
- Emergency fixes (use hotfix)
- Infrastructure setup (use infrastructure)

When in doubt, tag UP — pick the tag with more ceremony rather than less. Less-ceremony tags can be downgraded; more-ceremony tags ensure proper verify-phase attention.
</when-to-not-use>

<branch-prefix>
Single plan: `chore/{ticket-slug}`
Multi-plan:  `chore/{ticket-slug}-plan-{n}`
</branch-prefix>

</tag-recipe>
