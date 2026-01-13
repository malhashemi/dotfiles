#!/bin/bash
# Usage: ./worktree_cleanup.sh <plan-slug>
# Example: ./worktree_cleanup.sh plan-1-core-graph
# Output: Removes worktree and deletes local branch
# Exit: 0 on success, 1 if worktree doesn't exist

set -e

PLAN_SLUG="$1"

if [ -z "$PLAN_SLUG" ]; then
    echo "Usage: $0 <plan-slug>"
    exit 1
fi

WORKTREE_PATH=".trees/${PLAN_SLUG}"
BRANCH_NAME="implement/${PLAN_SLUG}"

if [ ! -d "$WORKTREE_PATH" ]; then
    echo "Error: Worktree does not exist at $WORKTREE_PATH"
    exit 1
fi

git worktree remove "$WORKTREE_PATH"
git branch -d "$BRANCH_NAME" 2>/dev/null || echo "Branch $BRANCH_NAME not found or not merged"
echo "Cleaned up worktree: $WORKTREE_PATH"
