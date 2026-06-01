<parallel-safety-criteria>

<overview>
Determines whether multiple plans (when D-phase identifies more than one) run in parallel worktrees or serialize in a single worktree.
</overview>

<decision-rule>
Default = sequential. Mark parallel-safe only when ALL four criteria clear.

| Criterion | Parallel-safe if... | Sequential-required if... |
|---|---|---|
| file-overlap | No two plans touch overlapping files | Any two plans touch the same files |
| logical-dependency | Plans have no output-input dependencies on each other | Plan B depends on plan A's outputs (types, schemas, APIs) |
| module-boundary | Plans entirely in different architectural seams (per ADRs) | Plans cross or share module boundaries |
| shared-infra | No shared infra files touched (migrations, package.json, build configs) | Any shared infra file touched |
</decision-rule>

<output-format>
Record the determination in the plan doc (or first-plan doc if multiple) as a `## Parallel-Safety` section:

```markdown
## Parallel-Safety

**Plans evaluated**: plan-1, plan-2, plan-3
**Decision**: parallel | sequential

**Evidence per criterion**:
- file-overlap: <pass | fail with file list>
- logical-dependency: <pass | fail with dependency arrows>
- module-boundary: <pass | fail with module names>
- shared-infra: <pass | fail with infra file list>
```
</output-format>

<downstream-effect>
| Decision | Worktree behavior |
|---|---|
| parallel | Separate worktree per plan: `{prefix}{ticket-slug}-plan-{n}` each |
| sequential | Single worktree: `{prefix}{ticket-slug}` (no `-plan-n` suffix); plans execute in dependency order |
</downstream-effect>

</parallel-safety-criteria>
