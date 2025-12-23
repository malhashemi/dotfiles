# Troubleshooting and Debugging

This guide covers debugging techniques and solutions to common chezmoi problems.

## Diagnostic Commands

### Quick Health Check

```bash
# Run comprehensive diagnostics
chezmoi doctor
```

Output shows:
- chezmoi version
- Configuration file location
- Source directory
- Destination directory
- Working copy (git status)
- Configuration issues
- Permission problems

### Verbose Output

```bash
# Show detailed operation info
chezmoi apply --verbose
chezmoi diff --verbose
chezmoi update --verbose

# Show what would happen (dry run)
chezmoi apply --dry-run --verbose
```

### Debug Mode

```bash
# Maximum verbosity with internal details
chezmoi apply --debug

# Debug with dry run
chezmoi apply --dry-run --debug
```

## Configuration Debugging

### Check Available Data

```bash
# Show all template data
chezmoi data

# Test specific template expression
chezmoi execute-template "{{ .chezmoi.hostname }}"
chezmoi execute-template "{{ .user.email }}"

# Test multiline template
chezmoi execute-template << 'EOF'
{{ .chezmoi.os }}
{{ .chezmoi.arch }}
EOF
```

### Verify Configuration

```bash
# Show effective configuration
chezmoi cat-config

# Edit configuration
chezmoi edit-config

# Configuration file location
~/.config/chezmoi/chezmoi.toml
```

### Test Template Rendering

```bash
# Preview file after template execution
chezmoi cat ~/.gitconfig
chezmoi cat ~/.zshrc

# Compare with actual file
diff <(chezmoi cat ~/.gitconfig) ~/.gitconfig
```

## File Debugging

### Check File Status

```bash
# List all managed files
chezmoi managed

# Check specific file status
chezmoi status ~/.zshrc

# Verify file matches source
chezmoi verify ~/.zshrc

# Show diff for file
chezmoi diff ~/.zshrc
```

### Source State Inspection

```bash
# Go to source directory
chezmoi cd

# Check source file
cat dot_gitconfig.tmpl

# Return to previous directory
exit
```

## Common Issues and Solutions

### Editor Issues

**Problem**: Editor opens and closes immediately

```bash
# Solution: Use --wait flag
export EDITOR="code --wait"
export EDITOR="vim -f"

# Or in config:
[edit]
  command = "code"
  args = ["--wait"]
```

**Problem**: Wrong editor opens

```bash
# Check current editor
echo $EDITOR

# Set temporarily
EDITOR=vim chezmoi edit ~/.zshrc

# Set permanently in config
[edit]
  command = "nvim"
```

### Template Errors

**Problem**: `template: :X:Y: executing "" at <.variable>: map has no entry for key "variable"`

**Solution**: Variable doesn't exist in data sources

```bash
# Check available data
chezmoi data | grep variable

# Add to config
chezmoi edit-config
# Add: [data]
#      variable = "value"

# Or to data file
# .chezmoidata.toml
variable = "value"
```

**Problem**: `bad character U+002D '-'`

**Solution**: Incorrect template syntax

```bash
# Wrong:
{{- if ... -}}

# Right:
{{ if ... -}}
```

**Problem**: `template: :X:Y: function "funcname" not defined`

**Solution**: Function doesn't exist

```bash
# Check function exists in:
# - Go text/template
# - Sprig functions
# - chezmoi-specific functions

# Common typos:
# "include" not "includeFile"
# "lookPath" not "which"
```

### Permission Issues

**Problem**: File permissions incorrect after apply

```bash
# Solution: Use attributes
chezmoi chattr +private ~/.ssh/config   # 600
chezmoi chattr +executable ~/.local/bin/script  # +x

# Or name with prefix:
# private_dot_ssh/config -> ~/.ssh/config (600)
# executable_script.sh -> script.sh (+x)
```

**Problem**: Group-writable files (SSH rejects)

```bash
# Solution: Set umask in config
[umask]
  value = 0o022  # Prevents group write
```

### Script Errors

**Problem**: Script won't execute

```bash
# Check shebang (must be first line, no blank lines before)
chezmoi cat ~/.local/share/chezmoi/run_script.sh | head -1

# Verify executable
ls -l ~/.local/share/chezmoi/run_script.sh

# Test manually
bash ~/.local/share/chezmoi/run_script.sh
```

**Problem**: Script runs every time (should be run_once)

```bash
# Check script naming
ls ~/.local/share/chezmoi/ | grep run_

# Clear state if needed
chezmoi state delete-bucket --bucket=scriptState
```

**Problem**: Script not running after changes

```bash
# For run_onchange: modify script to change hash
# Add comment with timestamp
# Updated: 2024-10-18

# Or clear state to force rerun
chezmoi state delete-bucket --bucket=entryState
```

### Git Issues

**Problem**: Changes not saving to repository

```bash
# Solution: Commit from source directory
chezmoi cd
git status
git add .
git commit -m "Update config"
git push
```

**Problem**: Can't pull from remote

```bash
# Check git status
chezmoi git status

# Check for conflicts
chezmoi cd
git status

# Resolve conflicts manually or:
git pull --rebase
# or
git pull --ff-only
```

**Problem**: Diverged from remote

```bash
# Force update from remote (discards local changes)
chezmoi cd
git fetch origin
git reset --hard origin/main

# Or merge changes
git pull --rebase
```

### Encryption Issues

**Problem**: Failed to decrypt

**For Age**:
```bash
# Check identity file exists
ls ~/.config/chezmoi/key.txt

# Verify in config
chezmoi cat-config | grep age

# Check permissions
chmod 600 ~/.config/chezmoi/key.txt
```

**For GPG**:
```bash
# Check key exists
gpg --list-secret-keys

# Check recipient in config
chezmoi cat-config | grep gpg

# Test decryption manually
gpg --decrypt file.asc
```

**Problem**: Encrypted file won't edit

```bash
# Check encryption config
chezmoi cat-config

# Verify file is marked encrypted
chezmoi cd
ls -l | grep encrypted_

# Try explicit encryption type
chezmoi edit --encryption=age ~/.ssh/id_rsa
```

### Password Manager Issues

**Problem**: Password manager function fails

```bash
# Check CLI installed
which op    # 1Password
which bw    # Bitwarden
which pass  # pass

# Check authentication
op account list
bw unlock

# Test retrieval manually
op read "op://vault/item/field"
bw get item itemname

# Check session environment
echo $OP_SESSION_*
echo $BW_SESSION
```

**Problem**: Timeout waiting for password manager

```bash
# Increase timeout in config
[timeout]
  password = "10m"  # 10 minutes
```

### State Issues

**Problem**: Persistent state lock

```bash
# Check for running instances
ps aux | grep chezmoi

# Kill if stuck
killall chezmoi

# Remove lock (use with caution!)
rm ~/.config/chezmoi/chezmoistate.boltdb-lock
```

**Problem**: State corruption

```bash
# Backup state
cp ~/.config/chezmoi/chezmoistate.boltdb ~/.config/chezmoi/chezmoistate.boltdb.backup

# Clear and rebuild
rm ~/.config/chezmoi/chezmoistate.boltdb
chezmoi init
chezmoi apply
```

### External File Issues

**Problem**: External not downloading

```bash
# Force refresh
chezmoi apply --refresh-externals

# Check URL accessibility
curl -I <url>

# Clear cache
rm -rf ~/.cache/chezmoi/
chezmoi apply -R
```

**Problem**: Archive extraction fails

```bash
# Test extraction manually
curl -L <url> | tar -tzf -

# Check stripComponents setting
# Download and inspect:
curl -L <url> | tar -tzf - | head
```

**Problem**: Wrong file from archive

```bash
# Check path in .chezmoiexternal.toml
# For archive-file type:
path = "correct/path/in/archive"

# List archive contents:
curl -L <url> | tar -tzf -
```

## Advanced Debugging

### Inspect State Database

```bash
# Dump entire state
chezmoi state dump

# Get specific bucket
chezmoi state get --bucket=scriptState
chezmoi state get --bucket=entryState

# Delete bucket (force re-run)
chezmoi state delete-bucket --bucket=scriptState
```

### Trace Template Execution

```bash
# Add debug output to templates
{{ printf "DEBUG: hostname = %s" .chezmoi.hostname }}
{{ printf "DEBUG: email = %s" .user.email }}

# Or use comments (visible in source only)
{{/* DEBUG: This section handles macOS config */}}
```

### Profile Performance

```bash
# Time operations
time chezmoi apply
time chezmoi diff

# Identify slow operations with --verbose
chezmoi apply --verbose 2>&1 | grep -E "took|duration"
```

### Compare States

```bash
# Show differences between source and destination
chezmoi diff

# Compare specific file
diff <(chezmoi cat ~/.zshrc) ~/.zshrc

# Show what would change
chezmoi apply --dry-run --verbose
```

## Environment-Specific Debugging

### macOS

```bash
# Check for SIP issues
csrutil status

# Verify permissions on home directory
ls -la ~

# Check for App Translocation
xattr -l /Applications/App.app
```

### Linux

```bash
# Check SELinux context
ls -Z ~/.local/bin/tool

# Restore context if needed
restorecon -v ~/.local/bin/tool

# Check AppArmor
aa-status
```

### Windows

```bash
# Check execution policy (PowerShell)
Get-ExecutionPolicy

# Set if needed
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Getting Help

### Gather Debug Information

When reporting issues, collect:

```bash
# Version info
chezmoi --version

# System info
uname -a  # or: sw_vers (macOS), lsb_release -a (Linux)

# Configuration
chezmoi cat-config

# Doctor output
chezmoi doctor

# Verbose output
chezmoi apply --dry-run --verbose
```

### Check Documentation

```bash
# Built-in help
chezmoi help
chezmoi help apply
chezmoi help edit

# Open documentation
open https://chezmoi.io/

# Search GitHub issues
open https://github.com/twpayne/chezmoi/issues
```

### Community Resources

- GitHub Issues: https://github.com/twpayne/chezmoi/issues
- Discussions: https://github.com/twpayne/chezmoi/discussions
- Documentation: https://chezmoi.io/

## Preventive Measures

### Regular Checks

```bash
# Run doctor periodically
chezmoi doctor

# Verify files match source
chezmoi verify

# Check for differences
chezmoi diff
```

### Safe Practices

```bash
# Always use dry run first
chezmoi apply --dry-run --verbose

# Preview changes
chezmoi diff

# Backup before major changes
tar czf ~/dotfiles-backup-$(date +%Y%m%d).tar.gz ~/.local/share/chezmoi/

# Test in VM or container first
```

### Maintain Clean State

```bash
# Commit changes regularly
chezmoi cd
git status
git add .
git commit -m "description"

# Keep scripts idempotent
# Make them safe to run multiple times

# Document machine-specific config
# Add comments explaining special cases
```
