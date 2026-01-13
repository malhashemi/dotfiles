# Validation Gates

## Gate Protocol

After each phase or parallel block, spawn Validator:

```
task({
  subagent_type: "validator",
  description: "Validate Phase N",
  prompt: "Validate Phase N from plan at [plan-path].
           
           Load skill(name='plan-validation') for protocol.
           Return PROCEED, PROCEED_WITH_NOTES, or BLOCKED."
})
```

## Handling Verdicts

| Verdict | Action |
|---------|--------|
| `PROCEED` | Continue to next phase |
| `PROCEED_WITH_NOTES` | Log notes, continue |
| `BLOCKED` | Stop, report to RPIV, wait for resolution |

## RPIV Trigger (Decomposition)

When Implement returns `NEEDS_DECOMPOSITION`:

1. **Create sub-plan worktree**:
   ```bash
   git worktree add .trees/{plan-slug}-phase-{N}-subplan -b implement/{plan-slug}-phase-{N}-subplan
   ```

2. **Trigger research**:
   ```
   task({
     subagent_type: "researcher",
     description: "Research Phase N decomposition",
     prompt: "Research requirements for Phase N decomposition.
              Original phase spec: [phase details]
              Why it's too big: [implement feedback]
              Return focused research for sub-planning."
   })
   ```

3. **Trigger sub-planning**:
   ```
   task({
     subagent_type: "planner",
     description: "Create sub-plan for Phase N",
     prompt: "Create sub-plan for Phase N.
              Research: [research output]
              Constraints: Must integrate back into parent plan.
              Return path to sub-plan."
   })
   ```

4. **Validate sub-plan**:
   ```
   task({
     subagent_type: "validator",
     description: "Review Phase N sub-plan",
     prompt: "Review sub-plan for Phase N.
              Load skill(name='plan-review').
              Return APPROVED or NEEDS_DECOMPOSITION."
   })
   ```

5. **Recursively orchestrate** the sub-plan

6. **Merge back**:
   ```bash
   gh pr create --base implement/{plan-slug} --head implement/{plan-slug}-phase-{N}-subplan --title "Phase N (decomposed)"
   gh pr merge {pr-number} --squash
   git worktree remove .trees/{plan-slug}-phase-{N}-subplan
   ```

## Error Handling

| Error | Action |
|-------|--------|
| Implement fails (not decomposition) | Review error, attempt fix, retry phase |
| Validation blocked | Stop, report to RPIV, wait for human input |
| Merge conflict | Resolve locally, re-validate, continue |
| Sub-plan fails | Escalate to RPIV, may need human intervention |
