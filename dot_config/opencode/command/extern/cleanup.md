---
description: Remove the .extern/ temporary workspace from current project
argument-hint: ""
agent: build
---

## Variables

### Static Variables

WORKSPACE: ".extern/"
RESEARCH_LOCATION: "thoughts/global/extern/"

## Instructions

Remove the temporary `.extern/` workspace from the current project.

### Phase 1: Check Workspace Exists

1. **Check if `{{WORKSPACE}}` exists** in current directory
2. **If not found**:
   - Inform user: "No `.extern/` workspace found in current project."
   - Exit successfully (nothing to clean)

### Phase 2: Show Current State

List what's currently in the workspace:

```bash
ls -la {{WORKSPACE}}
```

Present to user:
- Number of cloned repositories
- Total disk space used (approximate)

### Phase 3: Confirm Deletion

**IMPORTANT**: Ask user to confirm before deleting:

```
⚠️  This will delete the .extern/ workspace containing:
   - {n} cloned repositories
   - {size} of data

Research documents are preserved at:
   {{RESEARCH_LOCATION}}

Proceed with deletion? (yes/no)
```

**Wait for explicit confirmation** before proceeding.

### Phase 4: Delete Workspace

If user confirms:

```bash
rm -rf {{WORKSPACE}}
```

### Phase 5: Confirm Completion

Report success:

```
✅ Workspace cleaned up successfully!

Your research is preserved at:
   {{RESEARCH_LOCATION}}

To view your research catalog:
   /extern/catalog
```

## Important Notes

- **Always confirm** before deletion
- **Research is preserved** - Only the cloned repos are deleted
- **Idempotent** - Safe to run even if workspace doesn't exist
