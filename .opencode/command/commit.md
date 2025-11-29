---
description: Creates git commits with optional message, file filter, or splitting instructions
agent: build
argument-hint: "[optional: message, files, or instructions]"
---

# Commit Changes

## Variables

### Dynamic Variables
USER_INPUT: $ARGUMENTS

## Instructions

Create git commits for changes made during this session.

**If {{USER_INPUT}} looks like a commit message** (quoted string or conventional commit format like `feat:`, `fix:`, `chore:`):
- Use it as the commit message (or as a starting point to refine)

**If {{USER_INPUT}} specifies files or filters** (file paths, globs, or descriptions like "only the config files"):
- Focus commits on those files/areas only

**If {{USER_INPUT}} contains instructions** (like "split into two commits" or "separate refactoring"):
- Follow those instructions for commit organization

**If no {{USER_INPUT}} provided**:
- Analyze all changes and use your judgment on commit organization

## Workflow

### Phase 1: Analyze Changes

1. Run `git status` to see all changed files
2. Run `git diff` to understand modifications (staged and unstaged)
3. Review conversation history for context on what was accomplished
4. Consider whether changes should be one commit or multiple logical commits
5. Apply any {{USER_INPUT}} filters or instructions

### Phase 2: Plan Commits

1. Group related files that belong together
2. Draft clear, descriptive commit messages:
   - Use imperative mood ("Add feature" not "Added feature")
   - Focus on **why** the changes were made, not just what
   - Keep first line under 72 characters
3. Present plan to user:
   - List files for each commit
   - Show proposed commit message(s)
   - Ask: "I plan to create [N] commit(s). Shall I proceed?"

**⚠️ CHECKPOINT: Wait for user confirmation before executing**

### Phase 3: Execute Commits

1. Stage files with `git add <specific-files>` (**NEVER** use `-A` or `.`)
2. Create commits with planned messages
3. Show result with `git log --oneline -n [number of commits]`

## Critical Rules

- **NEVER** add co-author information or Claude attribution
- **NEVER** include "Generated with Claude" or "Co-Authored-By" lines
- **NEVER** use `git add -A` or `git add .` — always specify files explicitly
- Write commit messages as if the user wrote them
- Commits must be authored solely by the user

## Remember

You have full context of what was done this session. Group related changes, keep commits atomic, and trust your judgment — the user asked you to commit.
