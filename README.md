# Dotfiles

Cross-platform dotfiles managed by [chezmoi](https://chezmoi.io/) with a unified theming system for 21 applications.

![macOS](https://img.shields.io/badge/macOS-Primary-blue)
![Linux](https://img.shields.io/badge/Linux-Supported-green)
![Chezmoi](https://img.shields.io/badge/chezmoi-managed-orange)

## Features

- **Unified Theming** - 21 apps synchronized to one color scheme
- **Dual Theme Modes** - Static [Catppuccin](https://catppuccin.com/) or dynamic wallpaper-based colors
- **Cross-Platform** - Same repo works on macOS, headless Linux, and more
- **Fresh Install Ready** - One command installs packages, configs, and system settings
- **Progressive Enhancement** - Build what you need when you need it

## Quick Start

### Prerequisites

- Git with SSH key configured for GitHub
- [Bitwarden](https://bitwarden.com/) account (for secrets management)
- (Optional) [Tailscale](https://tailscale.com/) for cross-machine sync

### Installation

```bash
# Install chezmoi
brew install chezmoi  # macOS
# or: sh -c "$(curl -fsLS get.chezmoi.io)"  # Universal

# Initialize (installs packages, shows setup instructions)
chezmoi init git@github.com:malhashemi/dotfiles.git
```

### Secrets Setup (Required Before Apply)

Secrets are stored in Bitwarden and pulled by chezmoi. **Do this before `chezmoi apply`:**

```bash
# 1. Login to Bitwarden
bw login

# 2. Create persistent session (one-time)
bw unlock --raw > ~/.bitwarden_session
chmod 600 ~/.bitwarden_session
```

> **First time?** Create a Bitwarden item named `dotfiles-secrets` with custom fields for your API keys.
> See `~/.local/share/chezmoi/dot_secrets.example` for required fields.

### Apply Configuration

```bash
chezmoi diff    # Review changes
chezmoi apply   # Apply everything (secrets included)
```

### Post-Install (Optional)

```bash
gh auth login      # GitHub CLI authentication
atuin login        # Shell history sync
```

> **Note**: AeroSpace auto-starts at login and launches SketchyBar + Borders automatically.

---

## Theme System

The crown jewel of this repo. Change your wallpaper and watch 21 apps update their colors automatically.

### Commands

```bash
theme status                    # Show current theme state
theme set static                # Use Catppuccin (follows system light/dark)
theme set static --variant mocha  # Force specific variant
theme set dynamic               # Generate colors from current wallpaper
theme opacity 85                # Set transparency (0-100)
theme mode dark                 # Switch to dark mode
theme mode light                # Switch to light mode

wallpaper random                # Random wallpaper + auto-theme
wallpaper set ~/path/to/img.jpg # Set specific wallpaper
```

### How It Works

```
Wallpaper ──► matugen ──► Material Design 3 colors ──► 21 apps
                              │
                              ├── WezTerm (colors-wezterm.lua)
                              ├── NeoVim (colors/dynamic.lua)
                              ├── SketchyBar (colors-sketchybar.sh)
                              ├── Borders (bordersrc)
                              ├── Starship (inline TOML)
                              └── ... 16 more apps
```

### Theme Modes

| Mode | Source | Best For |
|------|--------|----------|
| **Static** | Catppuccin JSON (Mocha/Latte/Frappe/Macchiato) | Consistent, predictable colors |
| **Dynamic** | Wallpaper via [matugen](https://github.com/InioX/matugen) | Matching desktop aesthetic |

### Cross-Machine Sync

Sync your dynamic theme from Mac to headless servers:

```bash
# On Mac (with GUI + wallpaper)
theme push              # Sync to devbox

# On devbox (headless)
theme apply             # Apply received theme
```

GUI-only apps (WezTerm, Borders, SketchyBar) are automatically skipped on headless systems.

---

## Configured Applications

### Shell & Prompt
| App | Description | Themed |
|-----|-------------|:------:|
| [zsh](https://www.zsh.org/) + [Zinit](https://github.com/zdharma-continuum/zinit) | Shell with plugin manager | - |
| [Starship](https://starship.rs/) | Cross-shell prompt | ✓ |
| [Atuin](https://atuin.sh/) | Shell history with sync | ✓ |
| [Zoxide](https://github.com/ajeetdsouza/zoxide) | Smart directory jumper | - |

### Terminals
| App | Description | Themed |
|-----|-------------|:------:|
| [WezTerm](https://wezfurlong.org/wezterm/) | GPU-accelerated terminal | ✓ |
| [Ghostty](https://ghostty.org/) | Modern terminal emulator | ✓ |

### Editors
| App | Description | Themed |
|-----|-------------|:------:|
| [NeoVim](https://neovim.io/) | Hyperextensible editor (LazyVim) | ✓ |
| [Zed](https://zed.dev/) | High-performance editor | ✓ |
| [Neovide](https://neovide.dev/) | NeoVim GUI | ✓ |

### macOS Desktop
| App | Description | Themed |
|-----|-------------|:------:|
| [AeroSpace](https://github.com/nikitabobko/AeroSpace) | i3-like tiling window manager | - |
| [SketchyBar](https://github.com/FelixKratz/SketchyBar) | Custom menu bar | ✓ |
| [JankyBorders](https://github.com/FelixKratz/JankyBorders) | Window borders | ✓ |

### TUI Applications
| App | Description | Themed |
|-----|-------------|:------:|
| [lazygit](https://github.com/jesseduffield/lazygit) | Git TUI | ✓ |
| [yazi](https://github.com/sxyazi/yazi) | Terminal file manager | ✓ |
| [btop](https://github.com/aristocratos/btop) | System monitor | ✓ |
| [bottom](https://github.com/ClementTsang/bottom) | System monitor (alternative) | ✓ |
| [Television](https://github.com/alexpasmantier/television) | Fuzzy finder TUI | ✓ |
| [gitui](https://github.com/extrawurst/gitui) | Git TUI (alternative) | ✓ |
| [ncspot](https://github.com/hrkfdn/ncspot) | Spotify TUI | ✓ |
| [Posting](https://github.com/darrenburns/posting) | HTTP client TUI | ✓ |
| [CAVA](https://github.com/karlstav/cava) | Audio visualizer | ✓ |
| [glow](https://github.com/charmbracelet/glow) | Markdown renderer | ✓ |

### Development Tools
| App | Description | Themed |
|-----|-------------|:------:|
| [OpenCode](https://github.com/opencode-ai/opencode) | AI coding assistant | ✓ |
| [gh](https://cli.github.com/) | GitHub CLI | - |
| [Flameshot](https://flameshot.org/) | Screenshot tool | ✓ |
| [Obsidian](https://obsidian.md/) | Note-taking (per-vault) | ✓ |
| [Zen Browser](https://zen-browser.app/) | Firefox-based browser | - |

---

## Cross-Platform Architecture

### Platform Detection

Chezmoi automatically detects the platform and applies appropriate configs:

```go
// .chezmoi.toml.tmpl
is_mac = true/false       // macOS detection
is_linux = true/false     // Linux detection
is_headless = true/false  // No GUI (VPS, SSH-only)
```

### What Gets Installed Where

| Component | Mac | Headless Linux | Desktop Linux |
|-----------|:---:|:--------------:|:-------------:|
| Shell (zsh, Starship, Atuin) | ✓ | ✓ | ✓ |
| NeoVim | ✓ | ✓ | ✓ |
| TUI apps (lazygit, yazi, btop) | ✓ | ✓ | ✓ |
| Theme system | ✓ | ✓ (TUI only) | ✓ |
| WezTerm / Ghostty | ✓ | - | ✓ |
| AeroSpace / SketchyBar / Borders | ✓ | - | - |
| Zellij (terminal multiplexer) | - | ✓ | - |

### Target Systems

| System | Hostname Pattern | Status |
|--------|-----------------|--------|
| **Mac** (Primary) | Contains `MacBook` | ✅ Complete |
| **dev-box** (Arch VPS) | `dev-hub` | 🔲 Planned |
| **Desktop Arch** | TBD | 🔲 Future |
| **Windows** | TBD | 🔲 Future |

---

## Repository Structure

```
~/.local/share/chezmoi/
├── .chezmoi.toml.tmpl        # Platform detection & variables
├── .chezmoidata/
│   ├── apps.yaml             # App catalog (documentation)
│   └── user.yaml             # User preferences & theme settings
├── .chezmoiignore.tmpl       # Platform-based file filtering
├── .chezmoiscripts/          # Installation & setup scripts
│   ├── run_once_install-mac-packages.sh.tmpl
│   ├── run_onchange_after_macos-defaults.sh.tmpl
│   ├── run_onchange_after_zen-browser.sh.tmpl
│   └── run_onchange_after_theme.sh.tmpl
├── dot_config/
│   ├── theme-system/         # Unified theming engine
│   │   ├── scripts/
│   │   │   ├── apps/         # 21 app theme modules
│   │   │   ├── utils/        # Color math, hue generation
│   │   │   ├── theme-manager.py
│   │   │   └── wallpaper-manager.py
│   │   └── themes/           # Catppuccin JSON files
│   ├── aerospace/            # Window manager (macOS)
│   ├── nvim/                 # NeoVim (LazyVim config)
│   ├── wezterm/              # Terminal emulator
│   ├── sketchybar/           # Menu bar (macOS)
│   └── [30+ more apps]/
├── dot_zshrc.tmpl            # Shell configuration
├── dot_gitconfig.tmpl        # Git configuration
├── private_dot_ssh/          # SSH config (with Tailscale hosts)
├── private_Library/          # macOS LaunchAgents
├── Brewfile                  # Homebrew packages
└── justfile                  # Task runner commands
```

---

## Customization

### User Preferences

Edit `.chezmoidata/user.yaml`:

```yaml
user:
  name: "Your Name"
  email: "your@email.com"

preferences:
  default_theme: "mocha"           # mocha, latte, frappe, macchiato
  toggle_themes: ["mocha", "latte"] # For theme toggle command
  terminal:
    font_family: "JetBrains Mono"
    font_size: 16

theme_sync:
  enabled: true
  devbox_host: "your-server"       # Tailscale hostname
```

### Adding a New App to Theme System

1. Create `dot_config/theme-system/scripts/apps/myapp.py`:

```python
from .base import BaseApp

class MyAppTheme(BaseApp):
    requires_gui = False  # True if GUI-only
    
    def apply_theme(self, theme_data: dict) -> None:
        colors = theme_data["colors"]
        # Generate config file with colors
        content = f'background = "{colors["base"]}"\n'
        self.write_file(self.config_home / "myapp/theme.conf", content)
```

2. Register in `apps/__init__.py`:

```python
from .myapp import MyAppTheme

def get_all_apps(config_home):
    return [
        # ... existing apps
        MyAppTheme(config_home),
    ]
```

3. Add to `.chezmoiignore.tmpl` if the theme file is runtime-generated.

---

## Key Bindings (AeroSpace)

| Binding | Action |
|---------|--------|
| `Cmd + Enter` | New WezTerm window |
| `Alt + B` | Open Zen Browser |
| `Alt + O` | Open Obsidian |
| `Cmd + H/J/K/L` | Focus window (vim-style) |
| `Cmd + Shift + H/J/K/L` | Move window |
| `Cmd + 1-9` | Switch workspace |
| `Cmd + Shift + 1-9` | Move window to workspace |
| `Cmd + F` | Toggle fullscreen |
| `Cmd + M` | Toggle floating |
| `Cmd + Shift + W` | Random wallpaper + theme |

---

## macOS System Settings

Applied automatically via `run_onchange_after_macos-defaults.sh.tmpl`:

- **Dock**: Auto-hide enabled
- **Menu Bar**: Auto-hide enabled
- **Finder**: Show path bar, status bar, extensions; folders first
- **Keyboard**: Fast key repeat (for vim), full keyboard access
- **Screenshots**: Save to `~/Pictures/Screenshots`, no shadows
- **Text Input**: Disable smart quotes/dashes/autocorrect
- **Key Remap**: Caps Lock ↔ Escape (bidirectional swap)

---

## Acknowledgments

- [Catppuccin](https://catppuccin.com/) - Beautiful pastel color scheme
- [matugen](https://github.com/InioX/matugen) - Material Design 3 color generation
- [chezmoi](https://chezmoi.io/) - Dotfiles manager
- [LazyVim](https://www.lazyvim.org/) - NeoVim distribution

---

## License

MIT
