# Performance Optimization

This guide covers techniques for optimizing chezmoi's performance, especially important for large dotfile repositories or slow machines.

## Understanding Performance Impact

### What Slows Down Chezmoi

1. **External file downloads**: Checking URLs on every apply
2. **Password manager calls**: Retrieving secrets from external services
3. **Script execution**: Running scripts on every apply
4. **Template complexity**: Complex template logic and external commands
5. **Large file count**: Managing thousands of files
6. **Git operations**: Large repositories with extensive history

## External File Optimization

### Use Refresh Periods

```toml
# .chezmoiexternal.toml
[".oh-my-zsh"]
  type = "archive"
  url = "https://github.com/ohmyzsh/ohmyzsh/archive/master.tar.gz"
  refreshPeriod = "168h"  # Check weekly, not every apply
```

**Recommended periods**:
- Daily updates: `24h`
- Weekly updates: `168h`
- Monthly updates: `720h`
- Manual only: `0` (never check automatically)

### Minimize External Dependencies

```toml
# Bad: Many small external files (slow)
[".config/plugin1"]
  type = "file"
  url = "..."
[".config/plugin2"]
  type = "file"
  url = "..."
# ... 50 more

# Better: One archive with all plugins
[".config/plugins"]
  type = "archive"
  url = "https://example.com/all-plugins.tar.gz"
  refreshPeriod = "168h"
```

### Cache External Downloads

Externals are cached automatically:
```bash
# Cache location
~/.cache/chezmoi/

# Cache persists between applies
# Only re-downloads after refreshPeriod

# Force refresh when needed
chezmoi apply --refresh-externals
```

## Template Optimization

### Avoid External Commands in Templates

```bash
# Bad: Runs on every template evaluation
{{ output "complex-command" "arg1" "arg2" }}

# Better: Compute once in config template
# .chezmoi.toml.tmpl
[data]
  computed_value = {{ output "complex-command" | quote }}

# Use in other templates:
{{ .computed_value }}
```

### Minimize Password Manager Calls

```bash
# Bad: Call password manager in every file template
# dot_gitconfig.tmpl
[github]
  token = {{ onepasswordRead "op://vault/github/token" | quote }}

# dot_zshrc.tmpl
export GITHUB_TOKEN={{ onepasswordRead "op://vault/github/token" | quote }}

# dot_npmrc.tmpl  
//registry.npmjs.org/:_authToken={{ onepasswordRead "op://vault/github/token" | quote }}

# Better: Call once in config
# .chezmoi.toml.tmpl
[data.secrets]
  github_token = {{ onepasswordRead "op://vault/github/token" | quote }}

# Then reference in templates:
# dot_gitconfig.tmpl
[github]
  token = {{ .secrets.github_token | quote }}
```

### Use Template Fragments

```bash
# Instead of repeating complex logic:
# dot_zshrc.tmpl
{{ if eq .chezmoi.os "darwin" -}}
export HOMEBREW_PREFIX="/opt/homebrew"
eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"
{{ end -}}

# dot_bashrc.tmpl
{{ if eq .chezmoi.os "darwin" -}}
export HOMEBREW_PREFIX="/opt/homebrew"
eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"
{{ end -}}

# Better: Create template fragment
# .chezmoitemplates/homebrew-setup
{{ if eq .chezmoi.os "darwin" -}}
export HOMEBREW_PREFIX="/opt/homebrew"
eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"
{{ end -}}

# Reference in templates:
{{ template "homebrew-setup" . }}
```

### Simplify Conditional Logic

```bash
# Bad: Nested conditions repeated everywhere
{{ if eq .chezmoi.os "darwin" -}}
  {{ if eq .chezmoi.arch "arm64" -}}
    # config
  {{ else -}}
    # config
  {{ end -}}
{{ else if eq .chezmoi.os "linux" -}}
  {{ if eq .chezmoi.osRelease.id "ubuntu" -}}
    # config
  {{ end -}}
{{ end -}}

# Better: Derive platform variable in config
# .chezmoi.toml.tmpl
[data]
{{- if and (eq .chezmoi.os "darwin") (eq .chezmoi.arch "arm64") }}
  platform = "macos-arm"
{{- else if and (eq .chezmoi.os "darwin") (eq .chezmoi.arch "amd64") }}
  platform = "macos-intel"
{{- else if and (eq .chezmoi.os "linux") (eq .chezmoi.osRelease.id "ubuntu") }}
  platform = "ubuntu"
{{- else }}
  platform = "other"
{{- end }}

# Use simple comparison in templates:
{{ if eq .platform "macos-arm" -}}
# config
{{ end -}}
```

## Script Optimization

### Use Appropriate Script Types

```bash
# Bad: Runs every apply
run_always_install-packages.sh

# Better: Runs only when content changes
run_onchange_install-packages.sh

# Best: Runs once
run_once_install-packages.sh
```

### Avoid Unnecessary Scripts

```bash
# Bad: Script just to set environment variable
# run_after_set-var.sh
#!/bin/bash
export MY_VAR="value"

# Better: Set in shell config template
# dot_zshrc.tmpl
export MY_VAR="value"
```

### Make Scripts Conditional

```bash
# Bad: Script with internal conditional (always executes)
# run_after_macos-setup.sh
#!/bin/bash
if [ "$(uname)" = "Darwin" ]; then
  # setup
fi

# Better: Use .chezmoiignore to skip entirely
# .chezmoiignore
{{ if ne .chezmoi.os "darwin" }}
run_after_macos-setup.sh
{{ end }}

# Or template script:
# run_after_macos-setup.sh.tmpl
{{ if eq .chezmoi.os "darwin" -}}
#!/bin/bash
# setup
{{ end -}}
```

### Optimize Script Content

```bash
# Bad: Run expensive check every time
#!/bin/bash
brew update
brew upgrade

# Better: Check if update needed
#!/bin/bash
if [ $(( $(date +%s) - $(stat -f %m $(brew --prefix)) )) -gt 86400 ]; then
  brew update
  brew upgrade
fi
```

## File Management Optimization

### Use .chezmoiignore Effectively

```bash
# Bad: Manage files not needed on all machines
# Wastes time checking/applying

# Better: Ignore on irrelevant machines
# .chezmoiignore
{{ if ne .machine_class "development" }}
.local/share/large-dev-data/**
{{ end }}

{{ if ne .chezmoi.os "darwin" }}
.config/aerospace/**
{{ end }}
```

### Reduce Managed File Count

```bash
# Bad: Manage every file in large directory
chezmoi add ~/.config/app/**/*

# Better: Manage only configuration, use externals for plugins
chezmoi add ~/.config/app/config.toml
# Use .chezmoiexternal for plugins

# Or: Don't manage generated files
# .chezmoiignore
.config/app/cache/**
.config/app/logs/**
```

### Use Exact Directories Sparingly

```bash
# exact_ directories check all files on every apply
# Only use when necessary

# Bad: Exact on large directory that changes
exact_dot_cache/

# Better: Exact only on specific managed directories
exact_dot_config/exact_app/
```

## Configuration Optimization

### Optimize Data Files

```bash
# Bad: One large data file loaded every time
# .chezmoidata.toml (10000 lines)

# Better: Split into focused files
# .chezmoidata/common.yaml (100 lines)
# .chezmoidata/apps.yaml (50 lines)
# .chezmoidata/theme.yaml (50 lines)
```

### Minimize Configuration Size

```bash
# Bad: Inline large data in config
[data]
  large_list = ["item1", "item2", ..., "item1000"]

# Better: Store in separate data file
# .chezmoidata.toml
large_list = ["item1", "item2", ..., "item1000"]

# Or load from external source
# .chezmoiexternal.toml
[".local/share/data.json"]
  type = "file"
  url = "https://example.com/data.json"
  refreshPeriod = "168h"
```

## Git Optimization

### Shallow Clone

```bash
# For repositories you don't need full history
chezmoi init --depth 1 https://github.com/user/dotfiles.git

# Or in .chezmoiexternal.toml:
[".config/nvim"]
  type = "git-repo"
  url = "..."
  [".config/nvim".clone]
    args = ["--depth", "1"]
```

### Reduce Repository Size

```bash
# Remove large files from history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch large-file' \
  --prune-empty --tag-name-filter cat -- --all

# Or use git-filter-repo (faster)
git filter-repo --path large-file --invert-paths

# Garbage collect
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Optimize Git Configuration

```toml
# ~/.config/chezmoi/chezmoi.toml
[git]
  autoCommit = true   # Commit automatically
  autoPush = false    # But don't push (push manually when ready)
```

## Monitoring Performance

### Measure Apply Time

```bash
# Time full apply
time chezmoi apply

# Identify bottlenecks
chezmoi apply --verbose 2>&1 | grep -E "took|duration"

# Profile with dry run (faster)
time chezmoi apply --dry-run --verbose
```

### Monitor External Downloads

```bash
# Check cache size
du -sh ~/.cache/chezmoi/

# See what's cached
ls -lh ~/.cache/chezmoi/
```

### Track Script Execution

```bash
# Add timing to scripts
#!/bin/bash
START=$(date +%s)

# ... script content ...

END=$(date +%s)
echo "Script took $((END - START)) seconds"
```

## Platform-Specific Optimizations

### macOS

```bash
# Disable Spotlight indexing on source directory
mdutil -i off ~/.local/share/chezmoi

# Or add to Spotlight exclusions
# System Preferences > Spotlight > Privacy
# Add: ~/.local/share/chezmoi
```

### Linux

```bash
# Use faster diff tool
[diff]
  command = "delta"  # Or "difft"
  
# Enable parallel operations if supported
# (chezmoi operations are mostly serial, but git operations can parallelize)
```

### Windows

```bash
# Use Windows-native tools
[diff]
  command = "fc"  # Faster than external tools
  
# Optimize git for Windows
git config --global core.preloadindex true
git config --global core.fscache true
```

## Best Practices Summary

1. **Set refreshPeriod on all externals**: Avoid checking on every apply
2. **Minimize password manager calls**: Compute once in config template
3. **Use run_onchange or run_once**: Avoid run_always scripts
4. **Simplify templates**: Extract complex logic to config or fragments
5. **Ignore unnecessary files**: Use .chezmoiignore liberally
6. **Profile regularly**: Identify and fix bottlenecks
7. **Keep repository lean**: Remove large files and unnecessary history
8. **Cache external resources**: Let chezmoi cache do its job
9. **Use dry runs for testing**: Faster than actual applies
10. **Document slow operations**: So future you knows why they're necessary

## When Performance Doesn't Matter

Some operations are intentionally slow and that's OK:

- **Initial setup**: First apply on new machine can be slow
- **Major updates**: Refreshing all externals after config changes
- **Security-critical operations**: Password retrieval should be secure first
- **One-time migrations**: Moving to new patterns or cleaning up

Focus optimization efforts on:
- Daily operations (`chezmoi apply`)
- Common workflows (`chezmoi edit`, `chezmoi diff`)
- Machine sync (`chezmoi update`)

These should be fast enough to not disrupt your workflow.
