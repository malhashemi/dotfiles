# External File Management

This guide covers chezmoi's `.chezmoiexternal` system for managing files downloaded from external sources without storing them in your repository.

## Why Use Externals

External files solve several problems:

1. **Large files**: Don't bloat repository with binaries
2. **Third-party code**: Track dependencies without copying
3. **Downloaded resources**: Manage external tools and plugins
4. **Automatic updates**: Control when external content refreshes

## External Types

### Single Files

Download individual files from URLs:

```toml
# .chezmoiexternal.toml
[".vim/autoload/plug.vim"]
  type = "file"
  url = "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim"
  refreshPeriod = "168h"  # 1 week
```

**Common uses**:
- Editor plugins (vim-plug, etc.)
- Shell plugins
- Single-binary tools

### Archives

Download and extract tar/zip archives:

```toml
[".oh-my-zsh"]
  type = "archive"
  url = "https://github.com/ohmyzsh/ohmyzsh/archive/master.tar.gz"
  exact = true
  stripComponents = 1
  refreshPeriod = "168h"
```

**Options**:
- `exact = true`: Remove unmanaged files (like exact_ directories)
- `stripComponents = 1`: Remove top-level directory from archive
- `refreshPeriod`: How often to check for updates

**Common uses**:
- Oh My Zsh
- Frameworks
- Plugin collections

### Archive Files

Extract specific file(s) from archive:

```toml
[".local/bin/age"]
  type = "archive-file"
  url = "https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-{{ .chezmoi.os }}-{{ .chezmoi.arch }}.tar.gz"
  executable = true
  path = "age/age"
  refreshPeriod = "168h"
```

**Required fields**:
- `path`: Path within archive to extract

**Common uses**:
- Single binaries from archives
- Specific files from multi-file releases

### Git Repositories

Clone and manage Git repositories:

```toml
[".config/nvim"]
  type = "git-repo"
  url = "https://github.com/NvChad/NvChad.git"
  refreshPeriod = "168h"
  
[".config/nvim".clone]
  args = ["--depth", "1"]
  
[".config/nvim".pull]
  args = ["--ff-only"]
```

**Common uses**:
- Neovim configurations
- Custom tools
- Shared configurations

## Template Support

Make externals machine-specific using templates:

```toml
# .chezmoiexternal.toml.tmpl
[".local/bin/age"]
  type = "archive-file"
  url = "https://github.com/FiloSottile/age/releases/download/v{{ .age_version }}/age-v{{ .age_version }}-{{ .chezmoi.os }}-{{ .chezmoi.arch }}.tar.gz"
  executable = true
  path = "age/age"

{{ if eq .chezmoi.os "darwin" }}
[".config/aerospace"]
  type = "git-repo"
  url = "https://github.com/user/aerospace-config.git"
{{ end }}
```

## Advanced Features

### Include/Exclude Patterns

Filter archive contents:

```toml
["www/adminer/plugins"]
  type = "archive"
  url = "https://api.github.com/repos/vrana/adminer/tarball"
  stripComponents = 2
  include = ["*/plugins/**"]
  exclude = ["**/tests/**", "**/.git/**"]
```

### Checksums

Verify file integrity:

```toml
[".local/bin/tool"]
  type = "file"
  url = "https://example.com/tool"
  checksum.sha256 = "abc123def456..."
```

**Generate checksum**:
```bash
curl -L https://example.com/tool | shasum -a 256
```

### Decompression

Automatically decompress files:

```toml
[".local/bin/app"]
  type = "file"
  url = "https://example.com/app.gz"
  decompress = "gzip"  # or "bzip2", "xz"
  executable = true
```

### Filtering

Process file through command:

```toml
[".config/filtered"]
  type = "file"
  url = "https://example.com/config.json"
  filter.command = "jq"
  filter.args = [".data"]
```

**Common uses**:
- Extract from JSON: `jq .field`
- Process YAML: `yq .path`
- Transform content: `sed`, `awk`

### Encryption

Encrypt external files:

```toml
["private_dot_ssh/id_rsa"]
  type = "file"
  url = "https://example.com/keys/id_rsa"
  encrypted = true
```

## Refresh Management

### Refresh Period

Control update frequency:

```toml
refreshPeriod = "168h"   # 1 week
refreshPeriod = "24h"    # 1 day
refreshPeriod = "0"      # Never (manual only)
```

Without `refreshPeriod`, chezmoi checks on every apply (expensive).

### Manual Refresh

Force refresh regardless of period:

```bash
# Refresh all externals
chezmoi apply --refresh-externals
chezmoi apply -R

# Useful after updating .chezmoiexternal.toml
```

### Check External State

```bash
# Show managed externals
chezmoi managed | grep -v "^."

# Verify externals
chezmoi verify
```

## Common Patterns

### Editor Plugins

**Vim-Plug**:
```toml
[".vim/autoload/plug.vim"]
  type = "file"
  url = "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim"
  refreshPeriod = "168h"
```

**Neovim Config**:
```toml
[".config/nvim"]
  type = "git-repo"
  url = "https://github.com/NvChad/NvChad.git"
  refreshPeriod = "168h"
  [".config/nvim".clone]
    args = ["--depth", "1"]
```

### Shell Frameworks

**Oh My Zsh**:
```toml
[".oh-my-zsh"]
  type = "archive"
  url = "https://github.com/ohmyzsh/ohmyzsh/archive/master.tar.gz"
  exact = true
  stripComponents = 1
  refreshPeriod = "168h"
```

**Oh My Bash**:
```toml
[".oh-my-bash"]
  type = "git-repo"
  url = "https://github.com/ohmybash/oh-my-bash.git"
  refreshPeriod = "168h"
```

### Binary Tools

**Platform-specific binary**:
```toml
[".local/bin/age"]
  type = "archive-file"
  url = "https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-{{ .chezmoi.os }}-{{ .chezmoi.arch }}.tar.gz"
  executable = true
  path = "age/age"
  refreshPeriod = "168h"
```

**Compressed binary**:
```toml
[".local/bin/tool"]
  type = "file"
  url = "https://example.com/releases/tool-{{ .chezmoi.os }}.gz"
  decompress = "gzip"
  executable = true
  refreshPeriod = "168h"
```

### Fonts

```toml
[".local/share/fonts/FiraCode"]
  type = "archive"
  url = "https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip"
  include = ["ttf/*.ttf"]
  stripComponents = 1
  refreshPeriod = "720h"  # 30 days
```

### Configuration from APIs

```toml
[".config/app/servers.json"]
  type = "file"
  url = "https://api.example.com/servers"
  filter.command = "jq"
  filter.args = [".data"]
  refreshPeriod = "24h"
```

## Best Practices

1. **Set `refreshPeriod`**: Avoid checking on every apply
2. **Use checksums for binaries**: Verify integrity
3. **Template URLs**: Support multiple platforms
4. **Use `exact = true` carefully**: Removes unmanaged files
5. **Shallow clone git repos**: Faster with `--depth 1`
6. **Cache large downloads**: Externals are cached in chezmoi's cache directory
7. **Version pins**: Use specific versions in URLs for reproducibility
8. **Test refresh period**: Balance freshness vs. performance

## Troubleshooting

### External Not Updating

```bash
# Force refresh
chezmoi apply --refresh-externals

# Clear cache
rm -rf ~/.cache/chezmoi
chezmoi apply --refresh-externals
```

### Wrong File Permissions

```bash
# Make executable
[".local/bin/tool"]
  executable = true

# Make private
[".ssh/external_key"]
  private = true  # 600 permissions
```

### Archive Extraction Issues

```bash
# Check stripComponents value
# Download manually and inspect archive structure
curl -L <url> | tar -tzf - | head

# Count directory levels to strip
stripComponents = 1  # Remove first level
```

### Template Variables Not Available

Ensure `.chezmoiexternal.toml` has `.tmpl` suffix:
```bash
mv .chezmoiexternal.toml .chezmoiexternal.toml.tmpl
```

### Rate Limiting

GitHub API rate limits can affect downloads:

```bash
# Use authentication
# Set GitHub token
export GITHUB_TOKEN="ghp_..."

# Or use release URLs instead of API
url = "https://github.com/user/repo/releases/download/v1.0/file.tar.gz"
```

## Performance Considerations

### Reduce Apply Time

```bash
# Set reasonable refresh periods
refreshPeriod = "168h"  # Weekly check

# Avoid refreshPeriod = "0" (checks every time)

# Use --refresh-externals only when needed
chezmoi apply              # Normal apply
chezmoi apply -R           # With refresh
```

### Cache Location

Externals cache:
```bash
# Default cache location
~/.cache/chezmoi/

# Customize in config
[cache]
  dir = "~/.local/share/chezmoi/cache"
```

### Monitor External Size

```bash
# Check cache size
du -sh ~/.cache/chezmoi/

# Clean if needed
rm -rf ~/.cache/chezmoi/
```
