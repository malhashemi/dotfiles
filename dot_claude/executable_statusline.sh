#!/bin/bash

# Claude Code status line.
#
# Left-hand segments are translated from the active modules in
# ~/.config/starship/starship.toml:
#   - directory      -> ~ substitution
#   - git_branch      \_ single `git status --porcelain=2 --branch` call,
#   - git_status      /  colored by dirty state + a "✗" marker when dirty
#   - aws            -> read from env vars only (module is `disabled = false`)
#   - golang         -> file-presence check only (module has no `disabled`,
#                        format is icon-only, no version shown)
# `kubernetes` and `docker_context` are `disabled = true` in starship.toml,
# so they are intentionally omitted here.
#
# Right-hand segments (model / output style / context usage) are Claude
# Code-specific additions, not part of the starship translation.
#
# Kept fast: exactly one `git` subprocess (--no-optional-locks, read-only),
# no language-runtime subprocesses (no `go version`, `node --version`, no
# `aws` CLI or ~/.aws/config parsing).

# Read JSON input from stdin
input=$(cat)

# Extract values from JSON
current_dir=$(printf '%s' "$input" | jq -r '.cwd')
model=$(printf '%s' "$input" | jq -r '.model.display_name')
output_style=$(printf '%s' "$input" | jq -r '.output_style.name')

# Get directory name (similar to Starship's directory format)
# Replace home directory with ~ for cleaner display
display_dir="${current_dir/#$HOME/~}"

# Git information (matching Starship's git_branch + git_status modules)
# Use -C to operate on current_dir without changing the process cwd.
# --no-optional-locks avoids taking the index lock, and porcelain=2 --branch
# gets branch/upstream/dirty info in a single call.
git_info=""
if git -C "$current_dir" --no-optional-locks rev-parse --is-inside-work-tree &>/dev/null; then
    git_raw=$(git -C "$current_dir" --no-optional-locks status --porcelain=2 --branch 2>/dev/null)
    branch=$(printf '%s\n' "$git_raw" | awk '/^# branch\.head /{print $3}')
    oid=$(printf '%s\n' "$git_raw" | awk '/^# branch\.oid /{print substr($3,1,7)}')
    upstream=$(printf '%s\n' "$git_raw" | awk '/^# branch\.upstream /{print $3}')

    if [ -z "$branch" ] || [ "$branch" = "(detached)" ]; then
        branch_display="$oid"
    elif [ -n "$upstream" ] && [ "${upstream#*/}" != "$branch" ]; then
        # mirrors starship's `(:$remote_branch)` when local/remote names differ
        branch_display="$branch:${upstream#*/}"
    else
        branch_display="$branch"
    fi

    if printf '%s\n' "$git_raw" | grep -qE '^[12u?]'; then
        # dirty: palette red (#ffb4ab -> 256-color 217) + marker
        git_info=$(printf ' \033[38;5;217m%s ✗\033[0m' "$branch_display")
    else
        # clean: palette mauve/blue (#d5bbfc -> 256-color 183)
        git_info=$(printf ' \033[38;5;183m%s\033[0m' "$branch_display")
    fi
fi

# AWS info (matches starship's `aws` module, which is explicitly enabled).
# Env-vars only — no `aws` CLI call and no ~/.aws/config parsing, to stay fast.
aws_info=""
if [ -n "$AWS_PROFILE" ]; then
    region="${AWS_REGION:-$AWS_DEFAULT_REGION}"
    if [ -n "$region" ]; then
        aws_info=$(printf ' \033[1;34maws:%s(%s)\033[0m' "$AWS_PROFILE" "$region")
    else
        aws_info=$(printf ' \033[1;34maws:%s\033[0m' "$AWS_PROFILE")
    fi
fi

# Go project indicator (matches starship's `golang` module, which is
# enabled with an icon-only format — no version shown). File-presence check
# only, no `go version` subprocess.
go_info=""
if [ -f "$current_dir/go.mod" ] || [ -f "$current_dir/go.sum" ]; then
    go_info=$(printf ' \033[1;36mgo\033[0m')
fi

# Context window usage (shown when available)
used_pct=$(printf '%s' "$input" | jq -r '.context_window.used_percentage // empty')
ctx_info=""
if [ -n "$used_pct" ]; then
    used_int=$(printf '%.0f' "$used_pct")
    ctx_info=" \033[2m[ctx:${used_int}%]\033[0m"
fi

# Build status line: directory + git + aws + go, arrow, then model | output_style [ctx%]
printf '%s%s%s%s \033[1;32m➜\033[0m \033[2m%s | %s%s\033[0m' \
    "$display_dir" "$git_info" "$aws_info" "$go_info" "$model" "$output_style" "$ctx_info"