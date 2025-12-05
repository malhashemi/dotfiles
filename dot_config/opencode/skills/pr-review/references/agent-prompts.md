# Agent Prompt Templates

Templates for delegating to specialized agents during PR review workflow.

## Researcher Prompt Template

Use this template when delegating to the researcher agent in Phase 2:

```markdown
Analyze these PR review comments from @gemini-code-assist against our codebase.

## PR Context
- **Title**: {title from pr-info}
- **Description**: {body from pr-info}
- **Branch**: {headRefName} → {baseRefName}
- **Author**: {author.login}

## Review Comments to Assess

{For each unresolved comment:}
### Comment {N}
- **File**: `{path}:{line}`
- **Priority**: {extracted from badge - critical/high/medium/low}
- **Gemini's Issue**: {summary of comment body}
- **Thread ID**: {thread_id} (for reference)

<details>
<summary>Full comment</summary>
{complete comment body}
</details>

---

## Your Research Task

For EACH comment above:

1. **Understand PR Scope**: What is this PR trying to accomplish? What's in/out of scope?

2. **Technical Validity Check**:
   - Is Gemini's concern technically correct?
   - Read the actual code - does the issue exist as described?
   - Are there project-specific patterns that make this inapplicable?

3. **Scope Alignment Check**:
   - Does addressing this serve the PR's stated purpose?
   - Is this "scope creep" (valid but belongs in separate PR)?
   - Is this a "while you're here" suggestion?

4. **Recommendation** (one per comment):
   - ✅ **Address**: Valid concern, within scope, clear improvement
   - ❌ **Decline**: Invalid, by design, project-specific exception, or Gemini missing context
   - ⏸️ **Defer**: Valid but out of scope for this PR

## Output Format

Return your analysis as a structured table:

| # | File | Gemini Says | Your Assessment | Recommendation | Evidence |
|---|------|-------------|-----------------|----------------|----------|
| 1 | `path:line` | {issue} | {your technical evaluation} | ✅/❌/⏸️ | {codebase evidence} |

Then provide a summary:
- **To Address**: {count} items
- **To Decline**: {count} items (with brief reasoning for each)
- **To Defer**: {count} items (suggest where to track)
```

## Planner Prompt Template

Use this template when delegating to the planner agent in Phase 3:

```markdown
Create an implementation plan to address approved PR review feedback.

## Context
- **PR**: #{pr_number} - {title}
- **Branch**: {headRefName}
- **Repository**: {owner}/{repo}

## Approved Items to Address

{For each item the user approved:}
### Item {N}: {brief description}
- **File**: `{path}:{line}`
- **Issue**: {what needs to change}
- **Researcher's Analysis**: {relevant findings from researcher}
- **Thread ID**: {thread_id} (for tracking)

---

## Planning Requirements

1. **Minimal Changes**: Only modify what's necessary to address each item
2. **Preserve Patterns**: Follow existing code conventions in the codebase
3. **Test Coverage**: Include test updates if behavior changes
4. **No Scope Creep**: Don't "improve" unrelated code

## Expected Output

For each item, provide:
1. **Files to modify** with specific locations
2. **What to change** (be specific about the transformation)
3. **Why this approach** (brief rationale)
4. **Verification steps** (how to confirm it's fixed)

Then provide an execution order if dependencies exist between items.
```

## Implement Prompt Template

Use this template when delegating to the implement agent in Phase 4:

```markdown
Execute the implementation plan to address PR review feedback.

## Context
- **PR**: #{pr_number} - {title}
- **Branch**: {headRefName}
- **Commit Strategy**: Single commit with all changes

## Implementation Plan

{paste the plan from planner}

## Execution Requirements

1. **Follow the plan exactly** - don't add extra improvements
2. **Verify each change** - ensure it addresses the specific issue
3. **Run tests** after implementation: `{test_command}`
4. **Run build** to catch issues: `{build_command}`

## After All Changes

1. Stage all modified files
2. Commit with message:
   ```
   refactor: address PR review feedback
   
   - {brief description of item 1}
   - {brief description of item 2}
   ...
   ```
3. Push to the branch
4. Report back with:
   - Commit SHA
   - Files modified
   - Test/build results
   - Any issues encountered
```
