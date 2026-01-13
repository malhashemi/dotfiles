# PR Review Fixes Implementation Task

You are implementing fixes for approved items in PR #{{pr_number}}.

## Input

- **Assessment file**: `thoughts/shared/pr-reviews/{{pr_number}}/assessment.md`
- **Worktree**: {{worktree_path}}
- **Branch**: {{branch}}

## Your Task

Read the assessment file and implement ONLY items marked **Address**.

## CRITICAL: Implementation Rules

1. **MUST** read the assessment file first
2. **MUST** make minimal changes (don't over-engineer)
3. **MUST** follow the implementation notes from the assessment
4. **MUST** run tests after changes
5. **MUST** run build after changes
6. **MUST** commit with message format: "Address PR review feedback: {{summary}}"
7. **MUST** push to the PR branch
8. **MUST NOT** make changes beyond what's in the assessment

## Commit Message Format

```
Address PR review feedback: {{brief summary}}

- {{item 1 description}}
- {{item 2 description}}
```

## Output

Record your changes in: `thoughts/shared/pr-reviews/{{pr_number}}/changes.md`

Return message: "Implementation complete. Commit {{sha}} pushed to {{branch}}. {{n}} items addressed."
