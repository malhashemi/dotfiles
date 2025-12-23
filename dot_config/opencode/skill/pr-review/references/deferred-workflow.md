# Deferred Item Workflow

Detailed workflow for handling review comments that are valid but out of scope for the current PR.

## Label Management

Before creating issues for deferred items, ensure the `deferred` label exists:

```bash
# Check existing labels
gh label list

# Create if missing
gh label create deferred --description "Valid feedback deferred from PR review" --color FEF2C0
```

Or use the justfile recipe:
```bash
just -f {base_dir}/justfile ensure-label deferred "Valid feedback deferred from PR review" FEF2C0
```

## Issue Creation Template

Create a tracking issue with sufficient context for future work:

```bash
gh issue create \
  --title "{Descriptive title for the deferred work}" \
  --label "enhancement,deferred" \
  --body "## Background

Deferred from PR #{pr_number} review feedback by @{reviewer}.

## Problem

{Description of the issue from the review comment}

## Proposed Solution

{Suggested approach to address the concern}

## Reference

- PR #{pr_number} thread: {link_to_comment}
- File: \`{path}:{line}\`

## Priority

{Priority level - Low/Medium/High and suggested phase/milestone}"
```

### Template Fields

| Field | Source | Example |
|-------|--------|---------|
| `{title}` | Summarize the concern | "Add backup mechanism for config corruption" |
| `{pr_number}` | Current PR | 42 |
| `{reviewer}` | Comment author | gemini-code-assist |
| `{description}` | Expand on reviewer's concern | "The config loading silently fails..." |
| `{solution}` | Proposed fix approach | "Add backup before write, restore on parse failure" |
| `{link_to_comment}` | GitHub comment URL | `https://github.com/owner/repo/pull/42#discussion_r123` |
| `{path}:{line}` | File location from thread | `src/config.ts:216` |
| `{priority}` | Based on impact | "Medium - Data protection for Phase 5" |

## Complete Deferred Workflow

1. **Ensure label exists**
   ```bash
   just -f {base_dir}/justfile ensure-label deferred
   ```

2. **Create tracking issue**
   ```bash
   gh issue create --title "..." --label "enhancement,deferred" --body "..."
   # Returns: https://github.com/owner/repo/issues/123
   ```

3. **Reply to comment with issue link**
   ```bash
   just -f {base_dir}/justfile reply OWNER REPO PR_NUMBER COMMENT_ID \
     "⏸️ **Deferred**: Valid concern, but out of scope for this PR. Tracked in #123."
   ```

4. **Resolve the thread**
   ```bash
   just -f {base_dir}/justfile resolve THREAD_ID
   ```

## Already-Responded Threads

When processing unresolved threads, some may already have responses from previous review cycles:

| Prior Response | Action |
|----------------|--------|
| `✅ Addressed in commit...` | Verify commit exists, then resolve |
| `❌ Declined: ...` | Just resolve (decision already made) |
| `⏸️ Deferred: Tracked in #...` | Verify issue exists, then resolve |

To identify already-responded threads, check the comments data for `in_reply_to_id` fields—threads with replies from the PR author likely have prior responses.
