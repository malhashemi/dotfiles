# External Repositories Workspace

## Purpose

This directory holds temporarily cloned external repositories for pattern study and implementation research. These are NOT part of the project — they are disposable reference material.

## Status

This is a temporary workspace. Cloned repos here can be deleted at any time. All valuable research is persisted to the global extern catalog:

```
{thoughtsHome}/global/shared/extern/
├── catalog.md            # Global research index
└── repos/{org-repo}/     # Research documents
```

## For Agents

If you find yourself here, you are studying external code.

1. Check existing research first: read the global catalog before cloning.
2. Study with the read-only codebase children: codebase-pattern-finder
   (find implementations), codebase-analyzer (deep dive), codebase-locator
   (find files by purpose).
3. Persist findings to the global extern store, and update the catalog.

Do NOT store valuable notes in this directory. Do NOT modify cloned code —
it is read-only reference. Do NOT assume these clones persist.

## Cleanup

When research is done, this entire `.extern/` directory can be safely
deleted; persisted research in the global extern store survives.

```bash
rm -rf .extern/
```
