# Worktree Patterns

## Naming Conventions

| Work Type | Branch Name | Worktree Path |
|-----------|-------------|---------------|
| Plan | `implement/{plan-slug}` | `.trees/{plan-slug}` |
| Parallel phase | `implement/{plan-slug}-{phase-slug}` | `.trees/{plan-slug}-{phase-slug}` |
| Sub-plan | `implement/{plan-slug}-phase-{N}-subplan` | `.trees/{plan-slug}-phase-{N}-subplan` |

## The Rule

- **Sequential work** = commit (same branch)
- **Parallel work** = branch + worktree + PR

## Git Commands

### Create Plan Worktree
```bash
just -f {base_dir}/justfile worktree-create {plan-slug} {base-branch}
# Or directly:
git worktree add .trees/{plan-slug} -b implement/{plan-slug} {base-branch}
```

### Create Parallel Phase Worktree
```bash
git worktree add .trees/{plan-slug}-{phase-slug} -b implement/{plan-slug}-{phase-slug}
```

### Cleanup After PR Merge
```bash
just -f {base_dir}/justfile worktree-cleanup {plan-slug}
# Or directly:
git worktree remove .trees/{plan-slug}
git branch -d implement/{plan-slug}
```

## PR Workflow

### Create PR to Plan Branch
```bash
gh pr create --base implement/{plan-slug} --head implement/{plan-slug}-{phase-slug} --title "Phase N: {title}"
```

### Merge and Cleanup
```bash
gh pr merge {pr-number} --squash
git worktree remove .trees/{plan-slug}-{phase-slug}
```

### Final PR to Feature Branch
```bash
gh pr create --base {feature-branch} --head implement/{plan-slug} --title "{Plan Title}" --body "$(cat <<'EOF'
## Summary
- Phase 1: {description}
- Phase 2: {description}
...
EOF
)"
```
