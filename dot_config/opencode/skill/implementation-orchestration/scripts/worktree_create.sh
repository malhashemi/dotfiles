#!/bin/bash
# Usage: ./worktree_create.sh <plan-slug> <base-branch>
# Example: ./worktree_create.sh plan-1-core-graph polish
# Output: Creates .trees/<plan-slug> with branch implement/<plan-slug>
# Exit: 0 on success, 1 if worktree exists, 2 on git error

set -e

PLAN_SLUG="$1"
BASE_BRANCH="$2"

if [ -z "$PLAN_SLUG" ] || [ -z "$BASE_BRANCH" ]; then
    echo "Usage: $0 <plan-slug> <base-branch>"
    exit 1
fi

WORKTREE_PATH=".trees/${PLAN_SLUG}"
BRANCH_NAME="implement/${PLAN_SLUG}"

if [ -d "$WORKTREE_PATH" ]; then
    echo "Error: Worktree already exists at $WORKTREE_PATH"
    exit 1
fi

git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" "$BASE_BRANCH"
echo "Created worktree: $WORKTREE_PATH (branch: $BRANCH_NAME)"
