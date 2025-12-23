# Common Workflows and Patterns

This guide covers daily operations and proven patterns for managing dotfiles with chezmoi.

## Daily Operations

### Editing Files

```bash
# Edit source file in editor
chezmoi edit ~/.zshrc

# Edit and apply immediately on save
chezmoi edit --apply ~/.zshrc

# Watch for changes and apply automatically
chezmoi edit --watch ~/.zshrc

# Edit in specific editor
EDITOR=code chezmoi edit --apply ~/.gitconfig
```

### Previewing Changes

```bash
# Show diff of all changes
chezmoi diff

# Show diff for specific file
chezmoi diff ~/.zshrc

# Use custom diff tool
chezmoi diff --pager delta
chezmoi diff --pager "less -R"

# See what would change without applying
chezmoi apply --dry-run --verbose
```

### Applying Changes

```bash
# Apply all changes
chezmoi apply

# Apply with verbose output
chezmoi apply --verbose

# Dry run (no actual changes)
chezmoi apply --dry-run

# Apply specific file
chezmoi apply ~/.zshrc

# Apply and refresh externals
chezmoi apply --refresh-externals
```

### Adding Files

```bash
# Add file to chezmoi
chezmoi add ~/.gitconfig

# Add as template
chezmoi add --template ~/.zshrc

# Add as encrypted
chezmoi add --encrypt ~/.netrc

# Add as encrypted template
chezmoi add --encrypt --template ~/.aws/credentials

# Add directory
chezmoi add ~/.config/nvim

# Add directory recursively, removing unmanaged files
chezmoi add --exact ~/.config/app
```

### Removing Files

```bash
# Remove from chezmoi (keeps target file)
chezmoi forget ~/.gitconfig

# Remove file and delete from target
chezmoi remove ~/.unwanted_file

# List what would be removed
chezmoi remove --dry-run ~/.file
```

### Git Operations

```bash
# Work in source directory
chezmoi cd
git status
git add .
git commit -m "Update configuration"
git push
exit  # Return to original directory

# Or use chezmoi git subcommands
chezmoi git status
chezmoi git add .
chezmoi git commit -- -m "Update configuration"
chezmoi git push

# Update from remote repository
chezmoi update  # Pull and apply
chezmoi git pull -- --rebase
```

## Multi-Machine Workflow

### Setup New Machine

```bash
# Install chezmoi and initialize from repository
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply username

# Or with full URL
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply https://github.com/username/dotfiles.git

# With specific branch
chezmoi init --apply --branch=develop username/dotfiles
```

### Sync Between Machines

**Machine A** (make changes):
```bash
# Edit file
chezmoi edit ~/.zshrc
chezmoi apply

# Commit and push
chezmoi cd
git add .
git commit -m "Update zsh config"
git push
```

**Machine B** (get changes):
```bash
# Update (pull + apply)
chezmoi update

# Or step by step:
chezmoi git pull -- --autostash --rebase
chezmoi diff      # Review changes
chezmoi apply     # Apply changes
```

### Machine-Specific Configuration

**Pattern 1: Config file data**

Each machine has different config:
```toml
# work-laptop: ~/.config/chezmoi/chezmoi.toml
[data]
  machine_class = "work"
  email = "john@company.com"

# home-desktop: ~/.config/chezmoi/chezmoi.toml
[data]
  machine_class = "personal"
  email = "john@personal.com"
```

Use in templates:
```bash
# dot_gitconfig.tmpl
[user]
  email = {{ .email | quote }}
```

**Pattern 2: Hostname-based**

```go
# dot_zshrc.tmpl
{{ if eq .chezmoi.hostname "work-laptop" -}}
export WORK_ENV=true
{{ else if eq .chezmoi.hostname "home-desktop" -}}
export PERSONAL_ENV=true
{{ end -}}
```

**Pattern 3: Ignore files on certain machines**

```bash
# .chezmoiignore
{{ if ne .machine_class "work" }}
.work-config
{{ end }}

{{ if eq .chezmoi.os "windows" }}
.bashrc
.zshrc
{{ end }}
```

## File Management Patterns

### Private Files

```bash
# Files with mode 600
chezmoi add --private ~/.ssh/config
# Creates: private_dot_ssh/config

# Files with mode 700 (directories)
chezmoi add ~/.local/bin
# Creates: private_dot_local/bin/
```

### Executable Files

```bash
# Add executable script
chezmoi add ~/.local/bin/script.sh
# Creates: dot_local/bin/executable_script.sh

# Make existing file executable
chezmoi chattr +executable ~/.local/bin/tool
```

### Exact Directories

Remove unmanaged files from directory:

```bash
# Add as exact
chezmoi add --exact ~/.config/app
# Creates: exact_dot_config/exact_app/

# chezmoi will remove any files in ~/.config/app that aren't managed
```

### Symlinks

```bash
# Add symlink
chezmoi add ~/.config/symlink
# Creates: symlink_dot_config/symlink

# Template symlink target
# .chezmoitemplates/symlink_target.tmpl
{{ if eq .chezmoi.os "darwin" }}/usr/local{{ else }}/usr{{ end }}/bin/app
```

### Template Files

```bash
# Convert to template
chezmoi chattr +template ~/.gitconfig

# Remove template attribute
chezmoi chattr -template ~/.gitconfig

# Check file status
chezmoi status
```

## Common Configuration Patterns

### Shell Configuration

```bash
# dot_zshrc.tmpl
# OS-specific configuration
{{ if eq .chezmoi.os "darwin" -}}
export HOMEBREW_PREFIX="/opt/homebrew"
eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"
{{ else if eq .chezmoi.os "linux" -}}
export HOMEBREW_PREFIX="/home/linuxbrew/.linuxbrew"
[ -d "$HOMEBREW_PREFIX" ] && eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"
{{ end -}}

# Machine-specific environment
{{ if eq .machine_class "work" -}}
export COMPANY_PROXY="http://proxy.company.com"
{{ end -}}

# Common aliases (from template fragment)
{{ template "common-aliases" . }}
```

### Git Configuration

```bash
# dot_gitconfig.tmpl
[user]
  name = {{ .user.name | quote }}
  email = {{ .user.email | quote }}
{{ if eq .machine_class "work" -}}
  signingkey = {{ .git.work_key | quote }}
{{ else -}}
  signingkey = {{ .git.personal_key | quote }}
{{ end -}}

[core]
{{ if eq .chezmoi.os "windows" -}}
  autocrlf = true
{{ else -}}
  autocrlf = input
{{ end -}}

{{ if lookPath "delta" -}}
[core]
  pager = delta

[delta]
  navigate = true
  side-by-side = true
{{ end -}}
```

### SSH Configuration

```bash
# private_dot_ssh/config.tmpl
# Work servers
{{ if eq .machine_class "work" -}}
Host *.company.com
  User {{ .user.work_username }}
  ProxyCommand nc -X connect -x proxy.company.com:8080 %h %p
{{ end -}}

# GitHub
Host github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
{{ if eq .machine_class "work" -}}
  IdentityFile ~/.ssh/id_ed25519_work
{{ end -}}
```

### Application Configuration

```bash
# dot_config/app/config.toml.tmpl
[general]
theme = {{ .theme | quote }}
{{ if eq .chezmoi.os "darwin" -}}
font_size = 14
{{ else -}}
font_size = 12
{{ end -}}

[network]
{{ if eq .machine_class "work" -}}
proxy = {{ .network.proxy | quote }}
{{ end -}}
api_endpoint = {{ .api_endpoint | quote }}
```

## Troubleshooting Workflows

### Check System Health

```bash
# Run health check
chezmoi doctor

# Expected output shows configuration and any issues
```

### Verify Configuration

```bash
# Show available data
chezmoi data

# Test template execution
chezmoi execute-template "{{ .chezmoi.hostname }}"
chezmoi execute-template "{{ .user.email }}"

# Show computed file contents
chezmoi cat ~/.gitconfig
```

### Debug Differences

```bash
# Show diff
chezmoi diff

# Show verbose diff
chezmoi diff --verbose

# Check specific file
chezmoi verify ~/.zshrc

# List managed files
chezmoi managed
```

### Reset and Reapply

```bash
# Re-apply specific file
chezmoi apply --force ~/.zshrc

# Clear script state and reapply
chezmoi state delete-bucket --bucket=scriptState
chezmoi apply
```

## Collaboration Patterns

### Team Dotfiles

Share common configurations across team:

```bash
# Repository structure
dotfiles/
├── .chezmoidata/
│   ├── common.yaml        # Shared defaults
│   └── team.yaml          # Team-specific settings
├── .chezmoitemplates/
│   ├── company-git-config
│   └── company-ssh-config
├── dot_gitconfig.tmpl     # Uses team templates
└── README.md              # Setup instructions
```

**Team member setup**:
```bash
# Clone and initialize
chezmoi init --apply company/team-dotfiles

# Add personal overrides in local config
# ~/.config/chezmoi/chezmoi.toml
[data]
  personal_email = "me@personal.com"
```

### Testing Changes

```bash
# Use branches for experiments
chezmoi cd
git checkout -b test-feature

# Make changes
chezmoi edit ~/.zshrc
chezmoi apply

# Test...

# If good, merge
git checkout main
git merge test-feature
git push

# If bad, discard
git checkout main
git branch -D test-feature
chezmoi apply  # Revert to main branch config
```

### Documentation in Repository

```markdown
# README.md in dotfiles repo

## Quick Start

```sh
chezmoi init --apply https://github.com/username/dotfiles.git
```

## Requirements

- chezmoi >= 2.40
- age (for encrypted files)
- 1Password CLI (for secrets)

## Machine-Specific Setup

After initialization, configure machine-specific settings:

```sh
chezmoi edit-config
```

Add:
```toml
[data]
  machine_class = "work"  # or "personal"
  email = "your@email.com"
```

## Structure

- `.chezmoidata/`: Configuration data shared across machines
- `.chezmoiscripts/`: Setup scripts
- `.chezmoitemplates/`: Reusable template fragments

## Updating

```sh
chezmoi update  # Pull latest and apply
```
```

## Advanced Workflows

### Conditional File Installation

Only install files when certain conditions are met:

```toml
# .chezmoiexternal.toml.tmpl
{{ if and (eq .chezmoi.os "darwin") (lookPath "brew") -}}
[".config/aerospace"]
  type = "git-repo"
  url = "https://github.com/user/aerospace-config.git"
{{ end -}}
```

### Multi-Environment Support

Separate configurations for different environments:

```bash
# Use environment variable or config
# ~/.config/chezmoi/chezmoi.toml
[data]
  environment = "production"  # or "development", "staging"
```

```bash
# dot_config/app/config.toml.tmpl
{{ if eq .environment "production" -}}
[database]
  host = "prod-db.company.com"
{{ else if eq .environment "development" -}}
[database]
  host = "localhost"
{{ end -}}
```

### Automated Updates

```bash
# Cron job to auto-update daily (careful!)
0 9 * * * /usr/local/bin/chezmoi update --apply

# Or with confirmation:
0 9 * * * /usr/local/bin/chezmoi git pull && /usr/local/bin/chezmoi diff && read -p "Apply? (y/n) " -n 1 -r && [[ $REPLY =~ ^[Yy]$ ]] && /usr/local/bin/chezmoi apply
```

### Migration from Other Tools

**From GNU Stow**:
```bash
# Add stow-managed files
cd ~/dotfiles
for file in *; do
  chezmoi add ~/.$file
done
```

**From bare git repository**:
```bash
# Export current dotfiles
git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME ls-files | while read file; do
  chezmoi add ~/$file
done
```
