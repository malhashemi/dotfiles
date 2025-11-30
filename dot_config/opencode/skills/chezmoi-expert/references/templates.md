# Template System and Data Management

This guide covers chezmoi's powerful template system for creating machine-specific configurations from a single source.

## Template Creation

### Basic Template Commands

```bash
# Add new file as template
chezmoi add --template ~/.gitconfig

# Convert existing file to template
chezmoi chattr +template ~/.zshrc

# Test templates
chezmoi execute-template "{{ .chezmoi.hostname }}"
chezmoi execute-template < path/to/template.tmpl
```

## Data Sources

chezmoi provides multiple data sources, loaded in priority order:

### 1. Built-in Variables (`.chezmoi.*`)

Available automatically without configuration:

```go
{{ .chezmoi.os }}          # darwin, linux, windows
{{ .chezmoi.arch }}        # amd64, arm64, etc.
{{ .chezmoi.hostname }}    # machine hostname
{{ .chezmoi.username }}    # current user
{{ .chezmoi.homeDir }}     # home directory path
{{ .chezmoi.osRelease }}   # /etc/os-release (Linux)
{{ .chezmoi.sourceDir }}   # chezmoi source directory
{{ .chezmoi.version }}     # chezmoi version
```

### 2. Static Data Files (`.chezmoidata.$FORMAT`)

Place data files in source directory:

```toml
# ~/.local/share/chezmoi/.chezmoidata.toml
fontSize = 12
theme = "dark"

[user]
  name = "John Doe"
  email = "john@example.com"
```

Usage in templates:
```go
{{ .fontSize }}
{{ .theme }}
{{ .user.name }}
```

### 3. Data Directories (`.chezmoidata/`)

Organize data into multiple files:

```yaml
# .chezmoidata/apps.yaml
apps:
  editor: "nvim"
  shell: "zsh"
  browser: "firefox"
```

```yaml
# .chezmoidata/theme.yaml
colors:
  primary: "#007bff"
  secondary: "#6c757d"
```

Access in templates:
```go
{{ .apps.editor }}
{{ .colors.primary }}
```

### 4. Config File Data

Add data section to config file:

```toml
# ~/.config/chezmoi/chezmoi.toml
[data]
  email = "me@example.com"
  name = "John Doe"
  machine_type = "work"
```

## Template Syntax

chezmoi uses Go templates with additional functions.

### Conditionals

```go
{{/* OS-specific configuration */}}
{{ if eq .chezmoi.os "darwin" -}}
export BROWSER="open"
{{ else if eq .chezmoi.os "linux" -}}
export BROWSER="firefox"
{{ else if eq .chezmoi.os "windows" -}}
export BROWSER="start"
{{ end -}}

{{/* Hostname-based logic */}}
{{ if eq .chezmoi.hostname "workstation" -}}
export COMPANY_TOKEN="{{ onepasswordRead "op://Work/token" }}"
{{ end -}}

{{/* Machine type logic */}}
{{ if eq .machine_type "work" -}}
# Work-specific settings
{{ else -}}
# Personal settings
{{ end -}}
```

### Loops

```go
{{/* Iterate over list */}}
{{ range .apps -}}
export APP_{{ . | upper }}=1
{{ end -}}

{{/* Iterate with index */}}
{{ range $i, $app := .apps -}}
{{ $i }}: {{ $app }}
{{ end -}}

{{/* Iterate over map */}}
{{ range $key, $value := .colors -}}
export COLOR_{{ $key | upper }}="{{ $value }}"
{{ end -}}
```

### String Functions (Sprig)

chezmoi includes all Sprig functions:

```go
{{/* String manipulation */}}
{{ .email | upper }}                    # JOHN@EXAMPLE.COM
{{ .email | lower }}                    # john@example.com
{{ .path | replace "/" "\\" }}          # Windows paths
{{ .name | quote }}                     # "John Doe"
{{ .text | trim }}                      # Remove whitespace
{{ .text | trimPrefix "prefix-" }}      # Remove prefix
{{ .text | trimSuffix "-suffix" }}      # Remove suffix

{{/* Lists */}}
{{ list "a" "b" "c" | join "," }}       # a,b,c
{{ .items | first }}                    # First item
{{ .items | last }}                     # Last item
{{ .items | has "item" }}               # Check if contains

{{/* Paths */}}
{{ joinPath .chezmoi.homeDir ".config" "app" }}  # /home/user/.config/app
{{ base "/path/to/file.txt" }}                   # file.txt
{{ dir "/path/to/file.txt" }}                    # /path/to

{{/* Default values */}}
{{ .optional_value | default "fallback" }}
```

### Include Files

```go
{{/* Include another file's contents */}}
{{ include "dconf.ini" }}

{{/* Include with SHA for change detection */}}
# dconf.ini hash: {{ include "dconf.ini" | sha256sum }}
dconf load / < {{ joinPath .chezmoi.sourceDir "dconf.ini" | quote }}
```

### Template Fragments

Create reusable template fragments in `.chezmoitemplates/`:

```bash
# .chezmoitemplates/common-aliases
alias ll='ls -la'
alias g='git'
alias d='docker'
```

Use in templates:
```go
{{/* In dot_zshrc.tmpl */}}
{{ template "common-aliases" . }}
```

With parameters:
```bash
# .chezmoitemplates/git-config
[user]
  name = "{{ .name }}"
  email = "{{ .email }}"
```

```go
{{/* In dot_gitconfig.tmpl */}}
{{ template "git-config" dict "name" .user.name "email" .user.email }}
```

### Interactive Prompts

Prompt for values during initialization:

```go
{{/* In .chezmoi.toml.tmpl */}}
[data]
  email = {{ promptString "email" | quote }}
  name = {{ promptString "name" | quote }}
  enable_feature = {{ promptBool "enable_feature" }}
  
{{/* With defaults */}}
  editor = {{ promptString "editor" "vim" | quote }}
  
{{/* Only prompt once (stored in config) */}}
  {{ $email := promptStringOnce . "email" "Email address" -}}
  email = {{ $email | quote }}
```

### External Commands

Execute commands within templates:

```go
{{/* Output of command */}}
{{ output "hostname" "-f" }}

{{/* Conditional based on command */}}
{{ if lookPath "brew" -}}
# Homebrew is installed
{{ end -}}

{{/* Get path to executable */}}
#!{{ lookPath "bash" }}
```

## Template Debugging

### Test Template Rendering

```bash
# Test specific expressions
chezmoi execute-template "{{ .chezmoi.hostname }}"
chezmoi execute-template "{{ .apps.editor }}"

# Test file template
chezmoi cat ~/.gitconfig

# Show what data is available
chezmoi data

# Test with simulated prompts
chezmoi execute-template \
  --promptString email=test@example.com \
  '{{ promptString "email" }}'
```

### Common Template Errors

**Error**: `template: :X:Y: executing "" at <.variable>: map has no entry for key "variable"`
**Solution**: Variable doesn't exist. Check data sources or add to config.

**Error**: `bad character U+002D '-'`
**Solution**: Remove dash from template tag: `{{ if ... -}}` not `{{- if ... -}}`

**Error**: `template: :X:Y: function "funcname" not defined`
**Solution**: Function doesn't exist. Check Sprig docs or chezmoi-specific functions.

## Best Practices

1. **Use dashes for whitespace control**: `{{- ... -}}` removes surrounding whitespace
2. **Comment with `{{/* comment */}}`**: Standard Go template comments
3. **Keep templates readable**: Break complex logic into multiple conditionals
4. **Use template fragments**: Extract common patterns to `.chezmoitemplates/`
5. **Prefer data files over config**: Use `.chezmoidata/` for shared data
6. **Test before applying**: Use `chezmoi cat` or `execute-template` to verify
7. **Version control data files**: Commit `.chezmoidata/` to share across machines

## Advanced Patterns

### Machine Class Pattern

```toml
# Config per machine
[data]
  machine_class = "work"  # or "personal", "server"
```

```go
{{/* In templates */}}
{{ if eq .machine_class "work" -}}
# Work-specific config
{{ else if eq .machine_class "personal" -}}
# Personal config
{{ end -}}
```

### OS Family Pattern

```go
{{ if or (eq .chezmoi.os "darwin") (eq .chezmoi.os "linux") -}}
# Unix-like systems
{{ end -}}

{{/* Or create a variable */}}
{{ $isUnix := or (eq .chezmoi.os "darwin") (eq .chezmoi.os "linux") -}}
{{ if $isUnix -}}
# Unix config
{{ end -}}
```

### Feature Flags

```toml
# .chezmoidata.toml
[features]
  experimental = true
  beta_ui = false
```

```go
{{ if .features.experimental -}}
# Experimental features
{{ end -}}
```

### Derived Data

```toml
# .chezmoi.toml.tmpl
[data]
  email = "{{ .user.email }}"
  git_email = "{{ if eq .machine_class "work" }}{{ .user.email }}{{ else }}personal@example.com{{ end }}"
```
