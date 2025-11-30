# Multi-Machine Configuration Strategies

This guide covers proven strategies for managing dotfiles across multiple machines with different requirements.

## Core Concepts

### The Challenge

Different machines need different configurations:
- Work laptop vs personal desktop
- macOS vs Linux vs Windows
- Development machine vs server
- Home network vs corporate network

### The Goal

Maintain a single dotfiles repository that adapts to each environment while minimizing duplication.

## Strategy 1: Config File Data

Store machine-specific data in each machine's local config file.

### Setup

**Work Laptop** (`~/.config/chezmoi/chezmoi.toml`):
```toml
[data]
  machine_class = "work"
  email = "john@company.com"
  git_signing_key = "WORK_GPG_KEY"
  
[data.network]
  proxy = "http://proxy.company.com:8080"
  
[data.features]
  work_tools = true
  personal_apps = false
```

**Personal Desktop** (`~/.config/chezmoi/chezmoi.toml`):
```toml
[data]
  machine_class = "personal"
  email = "john@personal.com"
  git_signing_key = "PERSONAL_GPG_KEY"
  
[data.features]
  work_tools = false
  personal_apps = true
  gaming = true
```

### Usage in Templates

```bash
# dot_gitconfig.tmpl
[user]
  name = "John Doe"
  email = {{ .email | quote }}
  signingkey = {{ .git_signing_key | quote }}

{{ if eq .machine_class "work" -}}
[http]
  proxy = {{ .network.proxy | quote }}
{{ end -}}

# dot_zshrc.tmpl
{{ if .features.work_tools -}}
export PATH="$PATH:/opt/work-tools/bin"
{{ end -}}

{{ if .features.gaming -}}
export STEAM_DIR="$HOME/.steam"
{{ end -}}
```

### Pros & Cons

**Pros**:
- Clear separation of machine-specific data
- Easy to understand and maintain
- Config file not committed (can contain secrets)
- Changes don't require commits

**Cons**:
- Manual setup on each machine
- Config file not version controlled
- Easy to forget to update on new machine

## Strategy 2: Hostname-Based Logic

Use hostname to determine configuration.

### Setup

No per-machine config needed. Templates check hostname:

```bash
# dot_gitconfig.tmpl
[user]
  name = "John Doe"
{{ if eq .chezmoi.hostname "work-laptop" -}}
  email = "john@company.com"
  signingkey = "WORK_KEY"
{{ else if eq .chezmoi.hostname "home-desktop" -}}
  email = "john@personal.com"
  signingkey = "PERSONAL_KEY"
{{ else if eq .chezmoi.hostname "homelab-server" -}}
  email = "admin@homelab.local"
{{ end -}}
```

### Pros & Cons

**Pros**:
- Zero manual configuration
- Everything in version control
- Can't forget machine-specific settings

**Cons**:
- Hardcoded hostnames in repository
- Need to update templates for new machines
- Less flexible than config data

**Best for**: Small number of known machines

## Strategy 3: OS-Based Configuration

Adapt based on operating system and distribution.

### Setup

```bash
# dot_zshrc.tmpl
{{ if eq .chezmoi.os "darwin" -}}
# macOS specific
export HOMEBREW_PREFIX="/opt/homebrew"
eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"

{{ else if eq .chezmoi.os "linux" -}}
# Linux specific
{{ if eq .chezmoi.osRelease.id "ubuntu" -}}
# Ubuntu
export HOMEBREW_PREFIX="/home/linuxbrew/.linuxbrew"
{{ else if eq .chezmoi.osRelease.id "arch" -}}
# Arch Linux
export PATH="$PATH:/usr/local/bin"
{{ end -}}

{{ else if eq .chezmoi.os "windows" -}}
# Windows specific
{{ end -}}
```

### OS Release Data (Linux)

```bash
# Available on Linux from /etc/os-release:
{{ .chezmoi.osRelease.id }}              # ubuntu, arch, fedora
{{ .chezmoi.osRelease.versionID }}       # 22.04, etc.
{{ .chezmoi.osRelease.name }}            # Ubuntu
{{ .chezmoi.osRelease.prettyName }}      # Ubuntu 22.04 LTS
```

### Pros & Cons

**Pros**:
- Automatic detection
- No manual configuration
- Works across many machines

**Cons**:
- Only distinguishes by OS, not by purpose (work/personal)
- Requires testing on each OS

**Best for**: Dotfiles shared across different operating systems

## Strategy 4: Layered Data Files

Combine shared and machine-specific data.

### Setup

**Shared (committed)**:
```yaml
# .chezmoidata/common.yaml
common:
  editor: "nvim"
  shell: "zsh"
  
theme:
  colors:
    primary: "#007bff"
```

**Machine-specific (committed)**:
```yaml
# .chezmoidata/work.yaml
work:
  company: "ACME Corp"
  proxy: "http://proxy.company.com"
  
features:
  work_tools: true
  
# .chezmoidata/personal.yaml  
personal:
  projects_dir: "~/code"
  
features:
  gaming: true
```

**Local override (not committed)**:
```toml
# ~/.config/chezmoi/chezmoi.toml (in .chezmoiignore)
[data]
  machine_class = "work"  # Which data file to use
  email = "john@company.com"  # Secrets not in repo
```

### Usage

```bash
# dot_zshrc.tmpl
export EDITOR={{ .common.editor | quote }}

{{ if eq .machine_class "work" -}}
export http_proxy={{ .work.proxy | quote }}
{{ end -}}

{{ if .features.work_tools -}}
# Work tools config
{{ end -}}
```

### Pros & Cons

**Pros**:
- Shared data version controlled
- Machine-specific data organized
- Flexible combination of strategies

**Cons**:
- More complex structure
- Requires understanding of data precedence

**Best for**: Teams or multiple machines with shared base config

## Strategy 5: Conditional File Management

Don't just template file contents—control which files exist.

### Using .chezmoiignore

```bash
# .chezmoiignore
{{ if ne .machine_class "work" }}
.work-config/**
.config/work-vpn.conf
{{ end }}

{{ if ne .machine_class "personal" }}
.personal-config/**
.config/gaming/**
{{ end }}

{{ if eq .chezmoi.os "windows" }}
.bashrc
.zshrc
{{ end }}

{{ if ne .chezmoi.os "darwin" }}
.config/aerospace/**
.config/sketchybar/**
{{ end }}
```

### Machine-Specific Directories

```bash
# Repository structure:
dotfiles/
├── dot_config/
│   ├── common/          # Always installed
│   ├── work/            # Work-specific
│   └── personal/        # Personal-specific
├── .chezmoiignore       # Controls which config directories to use
```

### Pros & Cons

**Pros**:
- Clean - irrelevant files never created
- Fast - skipped files aren't processed
- Organized - clear separation in repo

**Cons**:
- Need to remember to update .chezmoiignore for new files
- Can't see ignored files in `chezmoi managed`

**Best for**: Distinct configurations per machine type

## Strategy 6: Machine-Specific Externals

Control external dependencies per machine.

### Setup

```toml
# .chezmoiexternal.toml.tmpl
{{ if .features.work_tools -}}
[".local/bin/work-cli"]
  type = "file"
  url = "https://internal.company.com/tools/cli"
  refreshPeriod = "168h"
{{ end -}}

{{ if .features.development -}}
[".config/nvim"]
  type = "git-repo"
  url = "https://github.com/user/nvim-config.git"
  refreshPeriod = "168h"
{{ end -}}

{{ if and (eq .chezmoi.os "darwin") .features.window_manager -}}
[".config/aerospace"]
  type = "git-repo"
  url = "https://github.com/user/aerospace-config.git"
{{ end -}}

{{ if .features.gaming -}}
[".local/share/steam-config"]
  type = "archive"
  url = "https://example.com/steam-settings.tar.gz"
  refreshPeriod = "720h"
{{ end -}}
```

### Pros & Cons

**Pros**:
- Don't download unnecessary externals
- Reduces apply time on machines that don't need them
- Clear feature flags

**Cons**:
- Requires setup of feature flags
- External URLs in version control

**Best for**: Large external dependencies that differ per machine

## Strategy 7: Interactive Initialization

Prompt for configuration on first setup.

### Setup

```bash
# .chezmoi.toml.tmpl
[data]
{{ $machine_class := promptString "machine_class" "work/personal/server" -}}
  machine_class = {{ $machine_class | quote }}
  
{{ $email := promptString "email" -}}
  email = {{ $email | quote }}
  
{{ if eq $machine_class "work" -}}
{{ $company := promptString "company" -}}
  company = {{ $company | quote }}
{{ end -}}

{{ $enable_gaming := promptBool "enable_gaming" -}}
[data.features]
  gaming = {{ $enable_gaming }}
```

### Usage

```bash
# First time on new machine:
chezmoi init https://github.com/user/dotfiles.git

# Prompts for:
# machine_class (work/personal/server): personal
# email: john@personal.com
# enable_gaming (y/n): y

# Creates ~/.config/chezmoi/chezmoi.toml with answers
```

### Pros & Cons

**Pros**:
- User-friendly setup
- No hardcoded hostnames
- Generates local config automatically

**Cons**:
- Can't fully automate setup
- Prompts can be interrupted

**Best for**: Dotfiles shared with others, new machine setup

## Strategy 8: Environment Variables

Use environment variables for dynamic configuration.

### Setup

```bash
# Before applying:
export DOTFILES_MACHINE_CLASS="work"
export DOTFILES_EMAIL="john@company.com"

chezmoi init --apply https://github.com/user/dotfiles.git
```

### Usage in Templates

```bash
# dot_gitconfig.tmpl
[user]
{{ if env "DOTFILES_EMAIL" -}}
  email = {{ env "DOTFILES_EMAIL" | quote }}
{{ else -}}
  email = "default@example.com"
{{ end -}}
```

### Pros & Cons

**Pros**:
- Good for CI/CD and automation
- No files to edit
- Easy to script

**Cons**:
- Environment variables not persistent
- Easy to forget to set
- No validation

**Best for**: Automated deployments, containers

## Recommended Combinations

### For Personal Use (2-3 Machines)

Combine **Strategy 1** (Config File Data) + **Strategy 3** (OS-Based):

```bash
# OS handles platform differences
{{ if eq .chezmoi.os "darwin" }}...{{ end }}

# Config data handles work/personal
{{ if eq .machine_class "work" }}...{{ end }}
```

### For Teams

Combine **Strategy 4** (Layered Data) + **Strategy 7** (Interactive Init):

```bash
# Shared team config in .chezmoidata/
# Interactive prompts create local config
# Team members get consistent base config
```

### For Many Machines

Combine **Strategy 2** (Hostname) + **Strategy 3** (OS) + **Strategy 5** (Conditional Files):

```bash
# OS handles platform differences
# Hostname handles known machines
# .chezmoiignore prevents irrelevant files
```

### For Servers

**Strategy 8** (Environment Variables) + minimal templates:

```bash
# Simple, scriptable
# Environment variables from deployment tools
# Minimal logic in templates
```

## Testing Strategies

### Test Multiple Configurations

```bash
# Temporarily override config
MACHINE_CLASS=work chezmoi apply --dry-run

# Test different OS (requires data)
CHEZMOI_OS=linux chezmoi execute-template < template.tmpl

# Preview specific config
chezmoi execute-template --init \
  --promptString machine_class=work \
  '{{ if eq .machine_class "work" }}work config{{ end }}'
```

### Use Branches for Machine Types

```bash
# Main branch: common config
# work branch: work-specific additions
# personal branch: personal additions

# Merge main into branches periodically
git checkout work
git merge main
```

## Migration Strategies

### From Simple to Complex

**Start**: Single config for all machines
```bash
# dot_gitconfig
[user]
  email = "john@example.com"
```

**Add**: OS detection
```bash
# dot_gitconfig.tmpl
{{ if eq .chezmoi.os "darwin" }}
# macOS stuff
{{ end }}
```

**Add**: Machine classes
```bash
# Add to config:
[data]
  machine_class = "work"

# Use in templates:
{{ if eq .machine_class "work" }}
{{ end }}
```

**Add**: Feature flags
```toml
[data.features]
  work_tools = true
  gaming = false
```

### From Other Tools

**From bare git repo**:
```bash
# Add machine detection gradually
chezmoi add --template ~/.gitconfig
# Add template syntax: {{ .chezmoi.os }}
```

**From GNU Stow**:
```bash
# Add files from stow structure
cd ~/dotfiles
for pkg in *; do
  for file in $pkg/*; do
    chezmoi add ~/."$(basename $file)"
  done
done
```

## Best Practices

1. **Start simple**: Use OS detection first, add complexity as needed
2. **Document your strategy**: README explains which approach you use
3. **Use consistent naming**: `machine_class`, `features`, etc.
4. **Validate configs**: Test on each machine type before committing
5. **Keep secrets local**: Never commit secrets to repository
6. **Use feature flags**: Better than machine-specific logic
7. **Layer your data**: Common -> OS-specific -> machine-specific
8. **Test in containers**: Verify cross-platform compatibility
9. **Version control smartly**: Commit shared data, not local config
10. **Keep it maintainable**: Optimize for clarity, not cleverness

## Troubleshooting Multi-Machine Setups

### Config Not Applied on Some Machines

```bash
# Check data available
chezmoi data | grep machine_class

# Verify template logic
chezmoi execute-template '{{ .machine_class }}'

# Test with different values
chezmoi execute-template --promptString machine_class=work \
  '{{ if eq .machine_class "work" }}YES{{ end }}'
```

### Files Not Ignored Correctly

```bash
# Preview what's ignored
chezmoi execute-template < .chezmoiignore

# Check specific file
chezmoi managed | grep filename
```

### Sync Issues Between Machines

```bash
# Check git status
chezmoi cd
git status

# Ensure local config not committed
cat .gitignore
# Should include: .chezmoi.toml or chezmoi.toml

# Pull latest
git pull
chezmoi apply
```
