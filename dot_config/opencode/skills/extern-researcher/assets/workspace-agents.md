# External Repositories Workspace

## Purpose

This directory contains temporarily cloned external repositories for pattern study and implementation research. **These are not part of the project** - they are reference material.

## Current Status

This is a **temporary workspace**. Cloned repos here can be deleted at any time. All valuable research is persisted to:

```
thoughts/global/extern/
├── catalog.md           # Global research index
└── repos/{org-repo}/    # Research documents
```

## For Agents

If you find yourself here, you're likely researching external code.

### Recommended Workflow

1. **Check existing research first**: Read `thoughts/global/extern/catalog.md`
2. **Use appropriate subagents**:
   - `codebase-pattern-finder` - Find similar implementations
   - `codebase-analyzer` - Deep dive on specifics
   - `codebase-locator` - Find files by purpose
3. **Persist findings**: Save to `thoughts/global/extern/repos/{org-repo}/`
4. **Update catalog**: Add study to global catalog

### Do NOT

- Store valuable notes in this directory
- Assume cloned repos will persist
- Modify code in cloned repos (they're read-only reference)

## Cleanup

When done with research, this entire `.extern/` directory can be safely deleted:

```bash
rm -rf .extern/
```

Research documents in `thoughts/global/extern/` will be preserved.
