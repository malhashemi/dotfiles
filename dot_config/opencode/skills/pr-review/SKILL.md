---
name: pr-review
description: |
  This skill provides a complete workflow for handling GitHub Pull Request reviews,
  specifically optimized for @gemini-code-assist automated reviews. This skill should
  be used when addressing PR review comments, responding to reviewers, resolving
  threads, requesting re-reviews, or merging PRs after feedback is addressed.
  Triggers include: /pr-review command, "address PR feedback", "handle review comments",
  "respond to gemini", or any PR review lifecycle management request.
---

# PR Review

## Overview

This skill enables efficient handling of GitHub Pull Request review workflows. It provides
Python scripts (via `uv run`) managed through a justfile for all GitHub API interactions,
along with structured workflows for analyzing, categorizing, and responding to review comments.

## When to Use

- User invokes `/pr-review` command
- Request to address PR feedback or review comments
- Need to respond to @gemini-code-assist review
- Requirement to resolve review threads or request re-review
- Request to merge PR after addressing feedback

## Scripts

All scripts are PEP 723 compliant Python files. The base directory for this skill is provided
when loaded. All scripts output JSON for easy parsing. Execute via justfile or directly with uv:

### Via Justfile (Recommended)

```bash
just -f {base_dir}/justfile <recipe> [args...]
```

| Recipe | Arguments | Description |
|--------|-----------|-------------|
| `pr-info` | `[pr_number]` | Get PR metadata (auto-detects if omitted) |
| `fetch-comments` | `owner repo pr_number` | Fetch inline review comments |
| `fetch-threads` | `owner repo pr_number` | Fetch threads with resolution status |
| `unresolved` | `owner repo pr_number` | Fetch only unresolved threads |
| `full-review` | `owner repo pr_number` | Get all PR data (info + threads + comments) |
| `reply` | `owner repo pr_number comment_id body` | Reply to a comment |
| `resolve` | `thread_id` | Resolve a thread by GraphQL ID |
| `request-review` | `owner repo pr_number body` | Post summary and request re-review |
| `merge` | `pr_number [method]` | Merge PR (method: merge/squash/rebase) |

### Direct Execution

```bash
uv run {base_dir}/scripts/<script>.py [args...]
```

| Script | Arguments | Description |
|--------|-----------|-------------|
| `get_pr_info.py` | `[pr_number]` | Get PR metadata (auto-detects if omitted) |
| `fetch_pr_comments.py` | `owner repo pr_number` | Fetch inline review comments |
| `fetch_review_threads.py` | `owner repo pr_number` | Fetch threads with resolution status |
| `reply_to_comment.py` | `owner repo pr_number comment_id body` | Reply to a comment |
| `resolve_thread.py` | `thread_id` | Resolve a thread by GraphQL ID |
| `request_review.py` | `owner repo pr_number body` | Post summary and request re-review |
| `merge_pr.py` | `pr_number [method]` | Merge PR (method: merge/squash/rebase) |

### Examples

```bash
# Via justfile
just -f {base_dir}/justfile pr-info 123
just -f {base_dir}/justfile fetch-threads owner repo 123
just -f {base_dir}/justfile unresolved owner repo 123

# Direct execution
uv run {base_dir}/scripts/get_pr_info.py 123
uv run {base_dir}/scripts/fetch_review_threads.py owner repo 123
```

## Comment Analysis Framework

### Priority Extraction

Gemini Code Assist uses badge images to indicate priority. To extract from comment body:

| Badge in Body | Priority | Action Required |
|---------------|----------|-----------------|
| `critical.svg` | Critical | Must address - blocks merge |
| `medium-priority.svg` | Medium | Should address - improves quality |
| `low-priority.svg` | Low | Optional - nice to have |

### Decision Categories

| Category | When to Apply | Response Template |
|----------|---------------|-------------------|
| **Address** | Valid concern improving code | `✅ **Addressed in commit {SHA}**\n\n{Details}` |
| **Decline** | Invalid, by design, or not applicable | `❌ **Declined**: {Reasoning}` |
| **Defer** | Valid but out of scope | `⏸️ **Deferred**: Will address in {issue/PR}` |

### Analysis Table Format

To present findings to user:

```markdown
## PR #{number} Review Analysis

Found {N} unresolved review comments.

| # | File | Issue | Priority | Recommendation | Reasoning |
|---|------|-------|----------|----------------|-----------|
| 1 | `path:line` | Description | Critical | ✅ Address | Why |
| 2 | `path:line` | Description | Medium | ❌ Decline | Why |

**Summary**: {X} to address, {Y} to decline
```

## Workflow Phases

### Phase 1: Gather

1. Determine PR number (from user request or auto-detect)
2. Extract OWNER/REPO from git remote: `git remote get-url origin`
3. Execute:
   ```bash
   just -f {base_dir}/justfile fetch-threads OWNER REPO PR_NUMBER
   just -f {base_dir}/justfile fetch-comments OWNER REPO PR_NUMBER
   ```
   Or use `unresolved` recipe to get only unresolved threads:
   ```bash
   just -f {base_dir}/justfile unresolved OWNER REPO PR_NUMBER
   ```
4. Parse results to identify unresolved threads

### Phase 2: Analyze

1. Parse each comment for priority badges
2. Formulate recommendation for each (address/decline/defer)
3. Present analysis table to user

**⚠️ CHECKPOINT - Wait for user approval before proceeding to implementation**

### Phase 3: Plan

After approval, delegate to planner agent via `session()` tool with:
- List of comments to address
- File paths and line numbers
- Issue descriptions

### Phase 4: Implement

Delegate to implement agent via `session()` tool with:
- Plan from planner
- Test/build requirements
- Commit message guidance

### Phase 5: Respond

For each addressed comment:
```bash
just -f {base_dir}/justfile reply OWNER REPO PR_NUMBER COMMENT_ID "✅ **Addressed in commit SHA**

Description of fix"
just -f {base_dir}/justfile resolve THREAD_ID
```

For declined comments (reply only, do not resolve):
```bash
just -f {base_dir}/justfile reply OWNER REPO PR_NUMBER COMMENT_ID "❌ **Declined**: Reasoning"
```

### Phase 6: Finalize

If comments were addressed:
```bash
just -f {base_dir}/justfile request-review OWNER REPO PR_NUMBER "## Review Feedback Summary

@gemini-code-assist All feedback addressed.

| # | Issue | Status |
|---|-------|--------|
| 1 | Description | ✅ Fixed in abc123 |

Please re-review."
```

If all declined and user approves merge:
```bash
just -f {base_dir}/justfile merge PR_NUMBER squash
```

## Error Handling

- **GitHub CLI auth failure**: Run `gh auth status` to verify authentication
- **PR not found**: Provide explicit PR number if auto-detect fails
- **GraphQL errors**: Verify thread ID format (should start with `PRRT_`)
- **Script errors**: Check `uv` is installed and available in PATH
- **Body quoting issues**: For complex bodies with special characters, use direct `gh api` calls:
  ```bash
  # Reply to comment with complex body
  gh api repos/OWNER/REPO/pulls/PR/comments \
    -f body=$'✅ **Addressed**\n\nDetails here' \
    -F in_reply_to=COMMENT_ID
  
  # Post PR comment
  gh pr comment PR --body "Simple message"
  ```
