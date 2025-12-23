# Script Execution

This guide covers chezmoi's script system for automating setup tasks, installing packages, and performing actions during dotfile application.

## Script Types and Execution

### Execution Order

Scripts execute in this order when running `chezmoi apply`:

```
1. run_before_* (sorted alphabetically)
2. File/directory updates
3. run_onchange_* (sorted alphabetically)  
4. run_once_* (sorted alphabetically)
5. run_after_* (sorted alphabetically)
```

### Script Prefixes

Scripts are identified by their filename prefix in the source directory:

```bash
# Always runs on every apply
run_always_script.sh

# Runs when script content changes
run_onchange_install-packages.sh

# Runs once (tracked in state)
run_once_setup.sh

# Timing: before file updates
run_before_preparation.sh

# Timing: after file updates  
run_after_cleanup.sh

# Combined prefixes
run_once_before_install-brew.sh
run_onchange_after_configure-app.sh
```

### Template Scripts

Add `.tmpl` suffix to make scripts templated:

```bash
run_onchange_install-packages.sh.tmpl
run_once_before_setup.sh.tmpl
```

**Example - OS-specific package installation**:
Template conditionals allow different commands per OS. The script content changes based on the OS, so it uses the appropriate package manager.

### run_onchange_*

Runs when script content changes. Ideal for:
- Package installation
- Configuration updates
- Dependency management

**Pattern: Embed file hashes to trigger on file changes**:
When you want a script to run whenever a related file changes, embed the file's hash in the script. When the file changes, the hash changes, making the script content different and triggering re-execution.

**Example: Install packages with Homebrew Bundle**:
The script includes a hash of the Brewfile. When packages are added/removed from Brewfile, the hash changes and brew bundle runs again.

**Example: Load system settings**:
When a settings file changes, reload it into the system. The hash comment ensures the script reruns when settings change.

### run_once_*

Runs once per machine, tracked in chezmoi state. Ideal for:
- Initial setup
- One-time configuration
- Installing tools

**Example: Setup SSH**:
Generate SSH key only if it doesn't exist. Use run_once so chezmoi doesn't try to generate it every time.

**Example: Clone repositories**:
Clone git repositories on first setup. Checks if directory exists before cloning to make it safe to rerun.

### run_before_*

Runs before applying file changes. Ideal for:
- Prerequisites
- Backup operations
- Dependency installation

**Example: Install package manager**:
On macOS, install Homebrew before any scripts try to use it. Uses run_before to ensure it's available for subsequent operations.

### run_after_*

Runs after applying file changes. Ideal for:
- Post-configuration
- Service restarts
- Cleanup

**Example: Reload shell configuration**:
After updating shell config files, reload them in the current session.

**Example: Restart services**:
After configuration changes, restart affected services to pick up new settings.

### run_always_*

Runs on every `chezmoi apply`. Use sparingly. Ideal for:
- Health checks
- Temporary cleanup
- Diagnostic output

**Example: Check critical tools**:
Verify that essential tools are available, warn if missing.

## Script Numbering

Use numeric prefixes to control execution order:

```bash
run_once_before_01-install-brew.sh
run_once_before_02-install-base-packages.sh
run_once_before_03-setup-configs.sh

run_after_99-cleanup.sh
```

Scripts execute alphabetically within their category, so numbering ensures consistent ordering.

## Script Environment

chezmoi sets environment variables for scripts:

```bash
# Always set by chezmoi
CHEZMOI=1
CHEZMOI_OS=darwin          # or linux, windows
CHEZMOI_ARCH=amd64         # or arm64, etc.
CHEZMOI_HOSTNAME=mymachine
CHEZMOI_SOURCE_DIR=/Users/user/.local/share/chezmoi
CHEZMOI_TARGET_DIR=/Users/user
CHEZMOI_USERNAME=user
```

**Add custom environment variables**:
```toml
# ~/.config/chezmoi/chezmoi.toml
[scriptEnv]
  CUSTOM_VAR = "value"
  API_ENDPOINT = "https://api.example.com"
```

**Access in scripts**:
```bash
#!/bin/bash
echo "Running on: $CHEZMOI_OS"
echo "Source dir: $CHEZMOI_SOURCE_DIR"
echo "Custom var: $CUSTOM_VAR"
```

## Error Handling

### Best Practices

```bash
#!/bin/bash

# Exit on error, undefined variables, pipe failures
set -euo pipefail

# Optional: Print commands as they execute (for debugging)
set -x

# Function for error messages
error() {
  echo "Error: $*" >&2
  exit 1
}

# Check prerequisites
command -v brew &> /dev/null || error "Homebrew not installed"

# Continue with script...
```

### Conditional Execution

```bash
# Run command only if it succeeds
if git clone repo.git; then
  echo "Clone successful"
else
  echo "Clone failed, continuing..."
fi

# Or use || for fallback
git pull || echo "Pull failed, continuing..."

# && for chaining
cd ~/repos && git clone repo.git
```

## Managing Script State

### View Script State

```bash
# Show all state
chezmoi state dump

# Check if script has run
chezmoi state get --bucket=scriptState script_name
```

### Clear Script State

```bash
# Clear run_once state (forces re-run)
chezmoi state delete-bucket --bucket=scriptState

# Clear specific script state
chezmoi state delete --bucket=scriptState script_name

# Clear run_onchange state (forces re-run)
chezmoi state delete-bucket --bucket=entryState
```

### Force Re-run

```bash
# Clear state and re-apply
chezmoi state delete-bucket --bucket=scriptState
chezmoi apply

# Or manually edit the script to change its hash
# Add a comment with timestamp:
# Updated: 2024-10-18
```

## Platform-Specific Scripts

Use `.chezmoiignore` to skip scripts on certain platforms:

```bash
# .chezmoiignore - skip brew script on non-macOS
```

Or use template conditionals within scripts to handle different platforms in one file.

## Common Patterns

### Install Homebrew Bundle

Create a Brewfile listing desired packages, then use run_onchange script with embedded file hash to install/update packages when the Brewfile changes.

### Install Node.js Packages

Loop through a list of global npm packages and install them. Use run_onchange with template to trigger when package list changes.

### Clone Git Repositories

Read repository URLs from configuration data and clone them if not already present. Use run_once to avoid re-cloning on every apply.

### Setup Programming Languages

Install and configure version managers (pyenv, nvm, rbenv) and set default language versions. Run once on initial setup.

### macOS Defaults

Set macOS system preferences using defaults command. Restart affected applications to apply changes. Run once on initial setup.

### Download and Install Binaries

Download releases from GitHub or other sources and install to local bin directory. Check if already installed to make idempotent.

## Debugging Scripts

### Verbose Output

```bash
# Run scripts with verbose output
chezmoi apply --verbose

# Show what scripts would run
chezmoi apply --dry-run --verbose
```

### Debug Mode

```bash
# Enable debug output
chezmoi apply --debug
```

### Test Scripts Independently

```bash
# Extract script to test
chezmoi cat ~/.local/share/chezmoi/run_once_script.sh > /tmp/test_script.sh
chmod +x /tmp/test_script.sh

# Run with environment
CHEZMOI_OS=darwin /tmp/test_script.sh
```

### Add Logging

Create a log directory and redirect script output to timestamped log files for troubleshooting.

## Best Practices

1. **Use `set -euo pipefail`**: Exit on errors, catch undefined variables
2. **Check prerequisites**: Verify required commands exist before using
3. **Make scripts idempotent**: Safe to run multiple times
4. **Use `run_onchange_` with hashes**: Trigger on file changes, not every apply
5. **Number scripts**: Control execution order with numeric prefixes
6. **Template conditionals**: Skip unsupported platforms gracefully
7. **Log important actions**: Help troubleshoot issues
8. **Avoid `run_always_`**: Use sparingly to avoid unnecessary work
9. **Test scripts**: Run manually before committing
10. **Use shebangs with `lookPath`**: Portable across systems
