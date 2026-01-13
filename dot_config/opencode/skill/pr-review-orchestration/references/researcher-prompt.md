# PR Review Assessment Task

You are assessing Gemini's review comments on PR #{{pr_number}}.

## Input

- **PR URL**: {{url}}
- **Branch**: {{branch}}
- **Worktree**: {{worktree_path}}
- **Unresolved threads**: {{thread_count}}

## Unresolved Threads

{{For each thread, format as:}}

### Thread {{N}}: `{{path}}:{{line}}`

**Thread ID**: `{{thread_id}}`
**Comment ID**: `{{comment_id}}`

**Gemini's Concern**:
> {{body}}

---

## CRITICAL: Research Requirements

For EACH thread, you **MUST**:

1. **MUST** spawn `codebase-analyzer` to read the actual code at `{{path}}:{{line}}`
2. **MUST** understand WHY the code was written this way
3. **MUST NOT** decide based solely on Gemini's description
4. **MUST** verify the concern against actual implementation
5. **MUST** provide evidence in your analysis that you read the code

**FORBIDDEN**:
- Making decisions without reading code
- Trusting Gemini's characterization without verification
- Lazy analysis that assumes knowledge

## Scope Creep Policy

Decision tree for each thread:

1. **Is the concern valid?** (requires code verification)
   - No evidence in code -> Decline with proof
   - Concern is valid -> Continue to step 2

2. **Is the fix trivial?** (< 5 lines, no new deps, no architecture change)
   - Trivial + useful -> Address (even if slight scope creep)
   - Non-trivial + out of PR scope -> Defer
   - Non-trivial + in PR scope -> Address

## Decision Categories

| Category | When to Use | Response |
|----------|-------------|----------|
| **Address** | Valid concern, fix is reasonable | Will be implemented |
| **Decline** | Invalid, by design, Gemini lacks context | Explain why |
| **Defer** | Valid but out of scope, needs separate work | Create issue |

## Output

Write your assessment to:
`thoughts/shared/pr-reviews/{{pr_number}}/assessment.md`

Use the exact format specified in references/assessment-format.md.

Return message: "Assessment complete. {{n}} threads analyzed: {{x}} Address, {{y}} Decline, {{z}} Defer. See assessment.md for details."
