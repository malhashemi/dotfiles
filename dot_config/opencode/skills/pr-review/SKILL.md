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

## Quick Reference

| Phase | Action | Command/Tool |
|-------|--------|--------------|
| 1 | Gather | `just -f {base_dir}/justfile unresolved OWNER REPO PR` |
| 2 | Research | `session({mode: "message", agent: "researcher", ...})` |
| 3 | Plan | `session({mode: "message", agent: "planner", ...})` |
| 4 | Implement | `session({mode: "message", agent: "implement", ...})` |
| 5 | Respond | `just reply ...` + `just resolve ...` |
| 6 | Finalize | `just request-review ...` or `just merge ...` |

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

## Multi-Agent Workflow

This skill orchestrates multiple specialized agents for thorough PR review analysis:

| Agent | Role | When Used |
|-------|------|-----------|
| **researcher** | Deep codebase analysis, independent assessment | Phase 2: Evaluates each comment against actual code |
| **planner** | Creates implementation plan | Phase 3: Plans approved changes |
| **implement** | Executes the plan | Phase 4: Makes code changes |

### Decision Categories

The researcher agent will recommend one of these for each comment:

| Category | Criteria | Response Template |
|----------|----------|-------------------|
| **✅ Address** | Valid concern, within PR scope, clear improvement | `✅ **Addressed in commit {SHA}**\n\n{Details}` |
| **❌ Decline** | Invalid, by design, project-specific exception, or Gemini missing context | `❌ **Declined**: {Reasoning}` |
| **⏸️ Defer** | Valid but out of PR scope, belongs in separate PR/issue | `⏸️ **Deferred**: Will address in {issue/PR}` |

### Priority Badge Reference

Gemini uses badge images to indicate its priority assessment (note: these reflect Gemini's view, not objective truth):

| Badge in Body | Gemini's Priority | Recommended Action |
|---------------|-------------------|-------------|
| `critical.svg` | Critical | Evaluate independently - may still decline |
| `high-priority.svg` | High | Evaluate independently |
| `medium-priority.svg` | Medium | Evaluate independently |
| `low-priority.svg` | Low | Often safe to defer |

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

### Phase 2: Research & Assess

Delegate deep analysis to the researcher agent using the session tool:

```
session({
  mode: "message",
  agent: "researcher",
  text: "<use Researcher Prompt Template from {base_dir}/references/agent-prompts.md>"
})
```

The researcher will:
1. Understand the PR's intended scope and purpose
2. Research the codebase for each comment's technical validity
3. Check for project-specific patterns Gemini might have missed
4. Return independent recommendations (✅ Address, ❌ Decline, ⏸️ Defer) with evidence

#### CHECKPOINT: User Approval Required

Present researcher's analysis and **wait for explicit approval** before proceeding.

User options:
- Approve all recommendations as-is
- Override specific decisions (e.g., "address #3 even though researcher said decline")
- Request more research on specific items

### Phase 3: Plan

After user approves the analysis, delegate to planner for items marked "Address":

```
session({
  mode: "message",
  agent: "planner",
  text: "<use Planner Prompt Template from {base_dir}/references/agent-prompts.md>"
})
```

The planner will:
1. Analyze each approved item's requirements
2. Determine the minimal changes needed
3. Create a step-by-step implementation plan
4. Define verification steps for each change

### Phase 4: Implement

Execute the plan from Phase 3:

```
session({
  mode: "message",
  agent: "implement",
  text: "<use Implement Prompt Template from {base_dir}/references/agent-prompts.md>"
})
```

The implement agent will:
1. Execute each step of the plan
2. Verify changes address the specific issues
3. Run tests and build
4. Commit and push changes
5. Report back with commit SHA

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

## Agent Prompt Templates

Templates for delegating to specialized agents are in `{base_dir}/references/agent-prompts.md`:

| Template | Used In | Purpose |
|----------|---------|---------|
| **Researcher** | Phase 2 | Deep codebase analysis, independent assessment of each comment |
| **Planner** | Phase 3 | Creates minimal implementation plan for approved items |
| **Implement** | Phase 4 | Executes plan, runs tests, commits and pushes |

Read the templates file when preparing session handoffs to each agent.

## Error Handling

- **GitHub CLI auth failure**: Run `gh auth status` to verify authentication
- **PR not found**: Provide explicit PR number if auto-detect fails
- **GraphQL errors**: Verify thread ID format (should start with `PRRT_`)
- **Script errors**: Check `uv` is installed and available in PATH
- **"not a git repository" error**: Justfile recipes that need git context (pr-info, merge, full-review) automatically run from the caller's directory. When running scripts directly, ensure execution is within a git repository
- **Body quoting issues**: For complex bodies with special characters, use direct `gh api` calls as an escape hatch (bypasses skill scripts):
  ```bash
  # Reply to comment with complex body
  gh api repos/OWNER/REPO/pulls/PR/comments \
    -f body=$'✅ **Addressed**\n\nDetails here' \
    -F in_reply_to=COMMENT_ID
  
  # Post PR comment
  gh pr comment PR --body "Simple message"
  ```
