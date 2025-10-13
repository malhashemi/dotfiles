---
date: 2025-10-13T21:20:00+00:00
author: claude  
status: draft
topic: "Unified Cross-Platform Dotfiles Migration Plan"
tags: [migration, chezmoi, dotfiles, macos, wsl, theme-system]
related_context:
  - thoughts/shared/research/2025-09-30_23-55-21_theme-system-architecture-and-constraints.md
  - thoughts/malhashemi/notes/caster/2025-10-12_17-59-18_unified-theming-system_context.md
---

# Unified Cross-Platform Dotfiles Migration Plan

## Executive Summary

Transform the current mixed Linux/Mac dotfiles repository into a clean, chezmoi-managed cross-platform configuration system focused on:
- **macOS** desktop environment (primary development machine)
- **WSL/Windows** support (future)
- **Cross-platform terminal apps** (WezTerm, kitty, neovim, starship, etc.)
- **Unified theme system** using matugen for Material You color generation

**Key Decision**: Linux ML4W setup remains independent and unmanaged by this repo.

## Current State

### Repository Contents

```
~/.local/share/chezmoi/
├── .config/                      # Linux ML4W configs (TO BE REMOVED)
│   ├── hypr/                     # Hyprland (Linux only)
│   ├── waybar/                   # Status bar (Linux only)
│   ├── rofi/                     # Launcher (Linux only)
│   ├── ml4w/                     # ML4W scripts (Linux only)
│   ├── matugen/                  # Color generator config
│   ├── wallust/                  # Alternative color generator
│   ├── kitty/                    # Terminal (cross-platform potential)
│   └── [22 more Linux-specific]
│
├── dot_config/                   # Mac configs (chezmoi-named)
│   └── theme-system/             # Legacy theme system (134MB with .git)
│       ├── .git/                 # TO BE REMOVED (flatten)
│       ├── themes/               # Catppuccin theme JSONs
│       ├── scripts/
│       │   ├── theme-manager.py
│       │   └── wallpaper-manager.sh
│       └── config.yaml
│
├── .bashrc                       # Linux ML4W version (TO BE REMOVED)
├── .zshrc                        # Linux ML4W version (TO BE REMOVED)
├── .gtkrc-2.0                    # Linux GTK config (TO BE REMOVED)
├── .Xresources                   # Linux X11 config (TO BE REMOVED)
│
└── .chezmoidata/                 # Empty (needs population)
```

### Issues

1. **Mixed Platform Files**: Linux and Mac configs coexist without proper separation
2. **No Chezmoi Structure**: Most files lack `.tmpl` extensions or platform suffixes
3. **Legacy Theme System**: Old architecture doesn't match new vision
4. **Git History Bloat**: `theme-system/.git` adds 134MB unnecessarily
5. **Missing Chezmoi Config**: No `.chezmoi.toml.tmpl` or `.chezmoiignore`

## Migration Strategy

### Phase 1: Repository Cleanup
**Goal**: Remove Linux-specific configs and flatten theme-system
**Status**: Ready to execute

### Phase 2: Chezmoi Foundation
**Goal**: Establish proper chezmoi structure and conventions
**Status**: Ready to execute

### Phase 3: New Theme System (Matugen-based)
**Goal**: Implement unified theming with Material You colors
**Status**: BLOCKED - waiting for ML4W matugen research

### Phase 4: WezTerm Integration
**Goal**: First application using new theme system
**Status**: BLOCKED - depends on Phase 3

### Phase 5: Expand Application Support
**Goal**: Add kitty, starship, neovim, etc.
**Status**: Future

---

## Phase 1: Repository Cleanup

### Overview
Clean the repository by removing all Linux-specific configurations and flattening the legacy theme-system's git history.

### Success Criteria

#### Automated Verification
- [x] Linux config directories removed: `rm -rf .config`
- [x] Root dotfiles removed: `.bashrc`, `.zshrc`, `.gtkrc-2.0`, `.Xresources` deleted
- [x] Theme-system git history removed: `.git` folder inside `dot_config/theme-system/` deleted
- [x] Repository size reduced significantly: `du -sh .` shows ~5MB or less
- [x] Git status clean: `git status` shows removals ready to commit

#### Manual Verification
- [x] No Linux-specific files remain in repository
- [x] Theme-system directory structure intact (just .git removed)
- [x] No broken references or symlinks

### Step-by-Step Instructions

#### 1.1 Backup Current State

```bash
# On Mac (chezmoi source directory)
cd ~/.local/share/chezmoi

# Create backup
cp -r . ~/dotfiles-backup-$(date +%Y%m%d)
echo "Backup created at ~/dotfiles-backup-$(date +%Y%m%d)"

# Verify backup
ls -lh ~/dotfiles-backup-*
```

#### 1.2 Remove Linux-Specific Directories

```bash
cd ~/.local/share/chezmoi

# Remove entire .config directory (all Linux ML4W configs)
rm -rf .config

# Verify removal
ls -la | grep -E "^d" | grep config
# Should only show: dot_config (Mac configs)
```

#### 1.3 Remove Linux Root Dotfiles

```bash
cd ~/.local/share/chezmoi

# Remove Linux-specific root files
rm -f .bashrc .zshrc .gtkrc-2.0 .Xresources

# Verify removal
ls -la | grep -E "^\."
# Should remain: .git, .gitignore, .chezmoidata, .opencode
```

#### 1.4 Flatten Theme-System Git History

```bash
cd ~/.local/share/chezmoi/dot_config/theme-system

# Check current size
du -sh .
# Expected: ~134MB due to .git

# Remove git history
rm -rf .git

# Verify removal
du -sh .
# Expected: <1MB

# Check directory still intact
ls -la
# Should show: themes/, scripts/, config.yaml, README.md, etc.
```

#### 1.5 Verify Repository Size

```bash
cd ~/.local/share/chezmoi

# Check total size
du -sh .
# Expected: ~5MB or less (down from ~135MB)

# Check git status
git status
# Should show deleted files ready to stage
```

#### 1.6 Commit Changes

```bash
cd ~/.local/share/chezmoi

# Stage removals
git add -A

# Review what's being removed
git status

# Commit with clear message
git commit -m "refactor: remove Linux ML4W configs and flatten theme-system

- Remove .config/ directory with all Linux-specific configs
- Remove Linux root dotfiles (.bashrc, .zshrc, .gtkrc-2.0, .Xresources)
- Flatten theme-system by removing .git subdirectory
- Reduces repo size from ~135MB to ~5MB
- Linux machine will remain independent with ML4W management
- Prepares repo for unified Mac/WSL/Windows management"

# Verify clean state
git status
```

### What We're NOT Doing

- **NOT touching Linux machine**: The Linux setup stays as-is with ML4W
- **NOT removing theme definitions**: Catppuccin theme JSONs remain
- **NOT removing theme scripts**: theme-manager.py and wallpaper-manager.sh remain (will be refactored later)
- **NOT removing dot_config directory**: Mac configs stay

### Rollback Plan

If something goes wrong:

```bash
# Restore from backup
cd ~
rm -rf ~/.local/share/chezmoi
cp -r ~/dotfiles-backup-YYYYMMDD ~/.local/share/chezmoi

# Re-initialize chezmoi
chezmoi init

# Verify state
cd ~/.local/share/chezmoi
git status
```

---

## Phase 2: Chezmoi Foundation

### Overview
Establish proper chezmoi configuration structure, data files, and conventions for cross-platform management.

### Changes Required

#### 2.1 Create `.chezmoi.toml.tmpl`

**File**: `.chezmoi.toml.tmpl`

```toml
{{- $hostname := .chezmoi.hostname -}}
{{- $os := .chezmoi.os -}}

[data]
    name = "{{ .chezmoi.username }}"
    hostname = "{{ $hostname }}"
    os = "{{ $os }}"
    
    {{- if eq $os "darwin" }}
    # macOS-specific settings
    is_mac = true
    is_linux = false
    is_wsl = false
    package_manager = "brew"
    config_home = "{{ .chezmoi.homeDir }}/.config"
    cache_dir = "{{ .chezmoi.homeDir }}/Library/Caches"
    
    {{- else if eq $os "linux" }}
    # Check if WSL
    {{- $is_wsl := or (env "WSL_DISTRO_NAME") (env "WSLENV") -}}
    is_mac = false
    is_linux = true
    is_wsl = {{ $is_wsl }}
    package_manager = "apt"  # or detect from system
    config_home = "{{ .chezmoi.homeDir }}/.config"
    cache_dir = "{{ .chezmoi.homeDir }}/.cache"
    
    {{- else if eq $os "windows" }}
    # Windows-specific settings
    is_mac = false
    is_linux = false
    is_wsl = false
    package_manager = "winget"
    config_home = "{{ .chezmoi.homeDir }}/AppData/Local"
    cache_dir = "{{ .chezmoi.homeDir }}/AppData/Local/Temp"
    {{- end }}

[diff]
    pager = "delta"

[merge]
    command = "nvim"
    args = ["-d", "{{ "{{" }} .Destination {{ "}}" }}", "{{ "{{" }} .Source {{ "}}" }}"]
```

**Purpose**: 
- Defines platform detection
- Sets up data variables for templates
- Configures chezmoi behavior

#### 2.2 Create `.chezmoiignore`

**File**: `.chezmoiignore`

```
# Ignore platform-specific configs on wrong platform

{{- if ne .chezmoi.os "darwin" }}
# Ignore macOS-specific configs on non-Mac
.config/aerospace/**
.config/sketchybar/**
.config/yabai/**
{{- end }}

{{- if ne .chezmoi.os "linux" }}
# Ignore Linux-specific configs on non-Linux
.config/hyprland/**
.config/sway/**
.config/waybar/**
.config/i3/**
{{- end }}

{{- if not .is_wsl }}
# Ignore WSL-specific configs when not in WSL
.config/wsl/**
{{- end }}

# Always ignore
.git/
.DS_Store
*.swp
*.bak
*~
.opencode/
thoughts/

# Extern directory (research repos, not deployed)
.extern/
```

**Purpose**:
- Prevents deploying wrong platform configs
- Keeps deployment clean and targeted

#### 2.3 Populate `.chezmoidata/`

**File**: `.chezmoidata/theme.yaml`

```yaml
# Current theme state (managed by theme-manager.py)
theme:
  name: "mocha"
  variant: "dark"
  transparency: 0
  platform: "darwin"
  colors:
    # Will be populated by theme-manager.py
    # For static themes: loaded from themes/catppuccin-*.json
    # For dynamic: generated by matugen
```

**File**: `.chezmoidata/user.yaml`

```yaml
# User preferences (manually edited)
preferences:
  default_theme: "mocha"
  
  # Wallpaper folders per theme
  wallpaper_folders:
    mocha: "~/Pictures/Wallpapers/dark"
    latte: "~/Pictures/Wallpapers/light"
    frappe: "~/Pictures/Wallpapers/dark"
    macchiato: "~/Pictures/Wallpapers/dark"
    dynamic: "~/Pictures/Wallpapers"
  
  # Application preferences
  terminal:
    font_family: "JetBrains Mono"
    font_size: 14
  
  # Toggle theme pair
  toggle_themes: ["mocha", "latte"]
```

**Purpose**:
- `theme.yaml`: Runtime theme state (generated by scripts)
- `user.yaml`: User customizations (manually edited)

#### 2.4 Create `.chezmoitemplates/`

**Directory**: `.chezmoitemplates/`

Reusable template fragments:

**File**: `.chezmoitemplates/theme-colors.tmpl`
```
{{- /* Shared color template fragment */ -}}
{{- if eq .theme.name "dynamic" }}
  {{- /* Dynamic colors from matugen */ -}}
{{- else }}
  {{- /* Static Catppuccin colors */ -}}
{{- end }}
```

**Purpose**: DRY - reusable template logic across configs

#### 2.5 Create `.chezmoiscripts/`

**Directory**: `.chezmoiscripts/`

Hooks for automated tasks:

**File**: `run_onchange_after_theme.sh.tmpl`
```bash
#!/bin/bash
# Reload applications after theme changes

{{- if eq .chezmoi.os "darwin" }}
# macOS app reloading
killall -SIGUSR1 kitty 2>/dev/null || true
killall -SIGUSR1 WezTerm 2>/dev/null || true
osascript -e 'tell application "System Events" to keystroke "r" using {command down, shift down}' 2>/dev/null || true

{{- else if eq .chezmoi.os "linux" }}
# Linux app reloading
killall -SIGUSR1 kitty 2>/dev/null || true
killall -SIGUSR2 waybar 2>/dev/null || true
hyprctl reload 2>/dev/null || true

{{- end }}

echo "✅ Applications reloaded"
```

**Purpose**: Automatically reload apps when configs change

### Success Criteria

#### Automated Verification
- [ ] Chezmoi config valid: `chezmoi doctor`
- [ ] Templates parse correctly: `chezmoi execute-template < .chezmoi.toml.tmpl`
- [ ] Data files load: `chezmoi data | jq .`
- [ ] Platform detection works: `chezmoi data | jq '.os'` shows "darwin"

#### Manual Verification
- [ ] `.chezmoi.toml.tmpl` exists and defines platform variables
- [ ] `.chezmoiignore` prevents wrong-platform configs from deploying
- [ ] `.chezmoidata/theme.yaml` and `user.yaml` exist
- [ ] `.chezmoitemplates/` contains reusable fragments
- [ ] `.chezmoiscripts/` contains reload hooks

---

## Phase 3: New Theme System (Matugen-based)

### Overview
**BLOCKED**: Waiting for research from ML4W dotfiles on matugen integration.

This phase will be detailed once we understand:
1. How ML4W configures matugen
2. What templates ML4W uses
3. How the color generation workflow works
4. Integration with wallpaper changes

### Placeholder Structure

**New theme-system architecture will include:**
- Integration with matugen for Material You colors
- Chezmoi templates for app configs
- Python orchestration script (PEP723)
- State management in `.chezmoidata/`

**Research in progress**: `/researcher/research-extern dotfiles` is analyzing ML4W's matugen setup.

---

## Phase 4: WezTerm Integration

### Overview
**BLOCKED**: Depends on Phase 3 (matugen research completion).

First application to implement with new theme system.

### Proposed Structure

```
dot_config/
└── wezterm/
    ├── wezterm.lua.tmpl      # Main config with OS conditionals
    └── colors.lua.tmpl       # Generated theme colors
```

**Details will be added** once matugen research completes.

---

## Phase 5: Expand Application Support

### Overview
Add remaining cross-platform applications after WezTerm proves the pattern.

**Applications**:
- kitty (terminal)
- starship (prompt)
- neovim (editor)
- btop (system monitor)
- zsh/bash (shells)

**Details**: TBD after Phase 4 completion.

---

## Migration Execution Order

### Immediate (Can Do Now)
1. ✅ **Phase 1**: Repository cleanup
2. ✅ **Phase 2**: Chezmoi foundation

### Blocked (Waiting on Research)
3. ⏳ **Phase 3**: New theme system (waiting for ML4W matugen research)
4. ⏳ **Phase 4**: WezTerm integration (depends on Phase 3)
5. ⏳ **Phase 5**: Additional apps (depends on Phase 4)

---

## Linux Machine Handling

### What Happens on Linux Machine

**Current State**: `~/dotfiles` contains copy of ML4W configs (not git-managed currently)

**Recommendation**:
```bash
# On Linux machine
cd ~/dotfiles

# Option A: Remove .git and keep as ML4W's territory
rm -rf .git
# ML4W will continue managing this directory

# Option B: Point to a separate ML4W-specific repo
mv ~/dotfiles ~/dotfiles.ml4w
git clone <your-ml4w-fork> ~/dotfiles.ml4w

# Option C: Keep as-is and leave unmanaged
# No changes needed - ML4W continues managing it
```

**This chezmoi repo will NOT manage the Linux desktop environment.**

---

## Testing Strategy

### Unit Testing (Per Phase)

**Phase 1 Tests**:
```bash
# Verify Linux configs removed
! test -d ~/.local/share/chezmoi/.config
# Verify theme-system .git removed
! test -d ~/.local/share/chezmoi/dot_config/theme-system/.git
# Verify size reduced
test $(du -s ~/.local/share/chezmoi | cut -f1) -lt 10000  # Less than ~5MB
```

**Phase 2 Tests**:
```bash
# Validate chezmoi config
chezmoi doctor
# Test template rendering
chezmoi execute-template < .chezmoi.toml.tmpl
# Verify data loads
chezmoi data | jq -e '.theme'
```

**Phase 4 Tests** (WezTerm):
```bash
# Verify WezTerm config renders
chezmoi execute-template < ~/.local/share/chezmoi/dot_config/wezterm/wezterm.lua.tmpl
# Test theme application
~/.config/theme-system/scripts/theme-manager.py set mocha
# Verify WezTerm reloads with new theme
```

### Integration Testing

After all phases:
```bash
# Fresh deployment test
chezmoi init --apply <your-repo-url>
# Verify all configs deployed correctly
ls -la ~/.config/wezterm
ls -la ~/.config/kitty
```

### Manual Testing Checklist

- [ ] Theme changes apply correctly to WezTerm
- [ ] Transparency toggle works
- [ ] Dynamic theme generates colors from wallpaper
- [ ] Apps hot-reload after theme change
- [ ] No error messages in terminal

---

## Performance Considerations

### Repository Size

**Before**: ~135MB (with theme-system .git)
**After Phase 1**: ~5MB
**Target**: Keep under 10MB

### Chezmoi Apply Time

**Target**: < 2 seconds for full deployment
**Monitor**: Use `time chezmoi apply` to track

### Theme Change Speed

**Target**: < 1 second to apply new theme
**Monitor**: Time theme-manager.py execution

---

## Rollback Strategy

### Per-Phase Rollback

**Phase 1**: Restore from backup
```bash
cd ~
rm -rf ~/.local/share/chezmoi
cp -r ~/dotfiles-backup-YYYYMMDD ~/.local/share/chezmoi
cd ~/.local/share/chezmoi
git reset --hard HEAD~1
```

**Phase 2**: Revert chezmoi commits
```bash
cd ~/.local/share/chezmoi
git log --oneline  # Find commit before Phase 2
git revert <commit-sha>
```

**Phase 3+**: Revert theme-system changes
```bash
# Restore old theme-system
cd ~/.local/share/chezmoi/dot_config
git checkout HEAD~1 -- theme-system/
```

### Emergency Full Rollback

```bash
# Mac: Stop managing with chezmoi
chezmoi unmanaged

# Restore original configs (if backed up)
cp -r ~/config-backup-YYYYMMDD ~/.config

# Clone fresh repo
cd ~/.local/share/chezmoi
git fetch origin
git reset --hard origin/main
```

---

## Success Metrics

### Phase 1 Success
- [ ] Repository size < 10MB
- [ ] No Linux-specific files remain
- [ ] Git history clean and committed

### Phase 2 Success
- [ ] `chezmoi doctor` passes
- [ ] Platform detection works
- [ ] Data files populate correctly

### Phase 3 Success
- [ ] Matugen integration understood
- [ ] Theme-system refactored to new architecture
- [ ] Color generation working

### Phase 4 Success
- [ ] WezTerm themed via chezmoi templates
- [ ] Theme changes apply < 1 second
- [ ] Hot reload works

### Overall Success
- [ ] Single repo manages Mac + WSL/Windows
- [ ] Theme system works across platforms
- [ ] Easy to add new applications
- [ ] Documentation complete

---

## Next Steps

1. **Execute Phase 1**: Repository cleanup (ready now)
2. **Execute Phase 2**: Chezmoi foundation (ready now)
3. **Wait for Research**: ML4W matugen analysis (in progress)
4. **Plan Phase 3**: Design new theme-system based on research
5. **Execute Phase 4**: Implement WezTerm with new system

---

## Questions & Decisions

### Confirmed Decisions
- ✅ Linux ML4W setup stays independent (not managed by this repo)
- ✅ Remove all Linux configs from this repo
- ✅ Flatten theme-system git history
- ✅ Focus on Mac + future WSL/Windows
- ✅ Start with WezTerm as first app

### Pending Decisions
- ⏳ After matugen research: Full replacement or evolution of theme-manager.py?
- ⏳ WSL support priority: Immediate or after Mac completion?
- ⏳ Additional apps: Which ones to prioritize after WezTerm?

---

## References

- Original theme system research: `thoughts/shared/research/2025-09-30_23-55-21_theme-system-architecture-and-constraints.md`
- New unified vision: `thoughts/malhashemi/notes/caster/2025-10-12_17-59-18_unified-theming-system_context.md`
- ML4W matugen research: **IN PROGRESS** at `thoughts/shared/extern/repos/dotfiles/`
- Chezmoi docs: https://www.chezmoi.io/
- Matugen docs: https://github.com/InioX/matugen
