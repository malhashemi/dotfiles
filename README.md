# Dotfiles

Cross-platform dotfiles managed by [chezmoi](https://chezmoi.io/): a full **Arch Linux + Hyprland** Wayland desktop and **macOS**, unified by a wallpaper-driven theming system across **34 applications** — everything from the login screen to your terminal follows one palette.

![Arch + Hyprland](https://img.shields.io/badge/Arch%20%2B%20Hyprland-Supported-1793D1)
![macOS](https://img.shields.io/badge/macOS-Supported-555555)
![Windows](https://img.shields.io/badge/Windows-Planned-lightgrey)
![Chezmoi](https://img.shields.io/badge/chezmoi-managed-orange)

## Features

- **Wallpaper-Driven Theming** — 34 apps recolored from one wallpaper, login screen included
- **Full Hyprland Desktop** — greetd login, Quickshell bar, Walker launcher, notifications, idle/lock, all themed
- **Voice Dictation** — local push-to-talk transcription (on-device) with a cloud smart layer + Arabic/English → English
- **AI Coding Environment** — a bundled [opencode](https://opencode.ai/) agent/skill framework (ticket → implement → PR review → merge)
- **Cross-Platform** — the same repo drives a Linux desktop, macOS, and headless servers
- **Fresh-Install Ready** — one command installs packages, configs, and system settings

## Quick Start

### Prerequisites

- Git with an SSH key configured for GitHub
- [Bitwarden](https://bitwarden.com/) account (for secrets)
- (Optional) [Tailscale](https://tailscale.com/) for cross-machine sync (prompted during init)

### Installation

```bash
# Install chezmoi
sh -c "$(curl -fsLS get.chezmoi.io)"   # universal
# or: brew install chezmoi             # macOS / Linuxbrew
# or: sudo pacman -S chezmoi           # Arch

# Initialize (prompts for platform + Tailscale, installs packages, prints next steps)
chezmoi init git@github.com:malhashemi/dotfiles.git
```

### Apply Configuration

```bash
chezmoi diff    # Review changes
chezmoi apply   # Apply dotfiles
```

### Secrets

Secrets live in Bitwarden and sync on-demand with the `secrets` command (all custom fields are auto-exported as environment variables):

```bash
secrets         # Sync from Bitwarden (handles login/unlock)
secrets -v      # Sync with masked value preview
secrets --help  # Setup instructions
```

> **First time?** Create a Bitwarden item named `dotfiles-secrets` with custom fields for your keys (e.g. `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GITHUB_TOKEN`). Override the item name/id with `BW_ITEM_NAME` / `BW_ITEM_ID` if you keep duplicates.

### Linux: switch on the login manager

The Arch installer sets up **greetd + regreet** but does **not** flip the display manager automatically (so you keep a TTY rollback path). When you're ready:

```bash
sudo systemctl disable sddm && sudo systemctl enable greetd && sudo reboot
```

### Post-Install (optional)

```bash
gh auth login      # GitHub CLI
atuin login        # Shell history sync
```

---

## The Hyprland Desktop (Linux)

A complete, themed Wayland desktop on Arch — written as native-Lua [Hyprland](https://hyprland.org/) config and managed by [uwsm](https://github.com/Vladimir-csp/uwsm). Everything below follows your wallpaper's palette via the theme system.

| Piece | What it is |
|-------|------------|
| **Compositor** | Hyprland (native Lua config) under a uwsm-managed session |
| **Login** | [greetd](https://git.sr.ht/~kennylevinsen/greetd) + [regreet](https://github.com/rharish101/ReGreet) in a `cage` kiosk — the **login screen follows your wallpaper** |
| **Status bar** | [Quickshell](https://quickshell.org/) bar: workspaces, window title, clock/calendar, CPU/mem/disk/volume/Wi-Fi, system tray, update count, media (MPRIS), theme controls, power menu |
| **Launcher** | [Walker](https://github.com/abenz1267/walker) (+ Elephant backend): apps, calculator, emoji, files, websearch, and **clipboard history** |
| **Notifications** | [swaync](https://github.com/ErikReider/SwayNotificationCenter) center with quick-toggles (Wi-Fi/BT/mute/lock) and do-not-disturb |
| **Power menu** | [wlogout](https://github.com/ArtsyMacaw/wlogout) (lock / logout / suspend / reboot / shutdown) |
| **Lock / idle** | hyprlock + hypridle (dim → lock → display-off → suspend) |
| **Wallpaper** | [awww](https://github.com/) daemon with animated transitions; a Quickshell wallpaper picker |
| **Voice HUD** | a click-through Quickshell overlay for voice dictation (see below) |

These start automatically with the graphical session via user services (`walker`, `elephant`, `voice-typerd`, `flameshot`, `swaync`).

**Extras:** system-wide mac-style editing chords (`ALT+C/V/X/A/Z`), a bilingual **US + Arabic** keyboard (toggle by pressing both `Ctrl` keys), touchpad workspace gestures, and per-app window rules. See [Key Bindings](#key-bindings) for the essentials, or press **`SUPER+K`** in the desktop for the full searchable cheatsheet.

---

## Voice Dictation (voice-typer)

Local, push-to-talk voice dictation — a self-hosted "Vibe Typer" replacement. Hold a hotkey, speak, and your words are transcribed **on-device** with [NVIDIA Parakeet](https://github.com/lucataco/parakeet-cli) and typed into the focused app, with an optional cloud (Gemini) smart layer and a live HUD.

| Hotkey (Linux) | Mode | What it does |
|----------------|------|--------------|
| `F7` | **local** | Raw transcript typed verbatim — instant, fully offline |
| `Ctrl+F7` | **dictate** | Transcript + AI cleanup (punctuation, fixes, self-corrections) |
| `Shift+F7` | **command** | Speak an instruction; the model acts on it and types the result |
| `Alt+F7` | **multilingual** | Speak Iraqi Arabic and/or English → fluent **English** |
| `Ctrl+Alt+V` | **paste-last** | Re-type the last dictation from disk (survives a clipboard miss) |

- **Hold** to talk, **release** to commit; **double-tap** to lock hands-free listening.
- **Screen-aware context:** the AI modes also feed the model your **focused app + window title**, current text selection, and a local **OCR of the active window** (tesseract) — or, optionally, a downscaled screenshot to a vision model (`screen_context = "ocr" | "screenshot" | "none"`). It's reference-only — used to spell on-screen names, code symbols, and filenames correctly — and the prompts forbid echoing it.
- Every result is saved to `~/.cache/voice-typer/last-response.txt`, so `paste-last` recovers it even if the clipboard moved on.
- **Never a silent failure:** on a cloud error, `dictate` falls back to the raw transcript; `command`/`multilingual` notify instead of typing nothing.
- macOS is supported (launchd + AeroSpace, toggle-style); needs `parakeet-cli` + model, `pi`, a `GEMINI_API_KEY`, and the usual capture/OCR tools — all wired into the installers.

---

## Theme System

The crown jewel. Change your wallpaper and **34 apps** — including the Hyprland desktop, the GTK/Qt app stack, and the login screen — recolor automatically.

### Commands

```bash
theme status                       # Show current theme state
theme set static                   # Catppuccin (follows system light/dark)
theme set static --variant mocha   # Force a variant
theme set dynamic                  # Generate colors from the current wallpaper
theme mode dark | light            # Switch light/dark
theme opacity 85                   # Transparency for UI surfaces (0-100)
theme refresh-backgrounds          # Re-render wallpaper-derived art (lock, login, logout)

wallpaper random                   # Random wallpaper + auto-theme (+ animated transition)
wallpaper set ~/path/img.jpg       # Set a specific wallpaper
wallpaper transition wave          # Choose the animated transition style
```

### How It Works

```
Wallpaper ──► matugen ──► Material Design 3 palette ──► 34 apps
                              ├── Hyprland / hyprlock / regreet (login)
                              ├── Quickshell bar + voice HUD
                              ├── Walker / swaync / wlogout
                              ├── GTK 3/4 + Qt (live light/dark)
                              ├── Ghostty / WezTerm / NeoVim / Starship
                              └── ... and the rest of the catalog
```

| Mode | Source | Best for |
|------|--------|----------|
| **Static** | [Catppuccin](https://catppuccin.com/) (Mocha/Latte/Frappé/Macchiato) | Consistent, predictable colors |
| **Dynamic** | Wallpaper via [matugen](https://github.com/InioX/matugen) | Matching the desktop aesthetic |

**Cross-machine sync:** `theme push` (from a GUI machine) → `theme apply` (on a headless box). GUI-only apps are skipped automatically on headless systems.

---

## Configured Applications

### Linux Desktop (Hyprland)
| App | Role | Themed |
|-----|------|:------:|
| [Hyprland](https://hyprland.org/) | Wayland compositor | ✓ |
| [Quickshell](https://quickshell.org/) | Status bar + voice HUD + wallpaper picker | ✓ |
| [Walker](https://github.com/abenz1267/walker) | App launcher + clipboard history | ✓ |
| [swaync](https://github.com/ErikReider/SwayNotificationCenter) | Notification center | ✓ |
| [wlogout](https://github.com/ArtsyMacaw/wlogout) | Power menu | ✓ |
| hyprlock / regreet | Screen lock / login greeter | ✓ |

### Shell & Prompt
| App | Description | Themed |
|-----|-------------|:------:|
| [zsh](https://www.zsh.org/) + [Zinit](https://github.com/zdharma-continuum/zinit) | Shell with plugin manager | - |
| [Starship](https://starship.rs/) | Cross-shell prompt | ✓ |
| [Atuin](https://atuin.sh/) | Shell history with sync | ✓ |
| [Zoxide](https://github.com/ajeetdsouza/zoxide) | Smart directory jumper | - |

### Terminals & Multiplexer
| App | Description | Themed |
|-----|-------------|:------:|
| [Ghostty](https://ghostty.org/) | Primary terminal emulator | ✓ |
| [WezTerm](https://wezfurlong.org/wezterm/) | GPU-accelerated terminal | ✓ |
| [Herdr](https://github.com/ogulcancelik/herdr) | Agent-aware terminal multiplexer (replaces Zellij) | ✓ |

### Editors
| App | Description | Themed |
|-----|-------------|:------:|
| [NeoVim](https://neovim.io/) (LazyVim) | Hyperextensible editor | ✓ |
| [Zed](https://zed.dev/) | High-performance editor (`$EDITOR` on desktop) | ✓ |
| [Neovide](https://neovide.dev/) | NeoVim GUI | ✓ |

### TUI Applications
| App | Description | Themed |
|-----|-------------|:------:|
| [lazygit](https://github.com/jesseduffield/lazygit) / [gitui](https://github.com/extrawurst/gitui) | Git TUIs | ✓ |
| [yazi](https://github.com/sxyazi/yazi) | File manager | ✓ |
| [btop](https://github.com/aristocratos/btop) / [bottom](https://github.com/ClementTsang/bottom) / [htop](https://htop.dev/) | System monitors | ✓ |
| [Television](https://github.com/alexpasmantier/television) | Fuzzy finder | ✓ |
| [ncspot](https://github.com/hrkfdn/ncspot) | Spotify TUI | ✓ |
| [Posting](https://github.com/darrenburns/posting) | HTTP client | ✓ |
| [CAVA](https://github.com/karlstav/cava) | Audio visualizer | ✓ |
| [peaclock](https://github.com/octobanana/peaclock) | Clock/timer | ✓ |
| [glow](https://github.com/charmbracelet/glow) | Markdown renderer | ✓ |

### macOS Desktop
| App | Description | Themed |
|-----|-------------|:------:|
| [AeroSpace](https://github.com/nikitabobko/AeroSpace) | Tiling window manager | - |
| [SketchyBar](https://github.com/FelixKratz/SketchyBar) | Menu bar | ✓ |
| [JankyBorders](https://github.com/FelixKratz/JankyBorders) | Window borders | ✓ |

### Tools
| App | Description | Themed |
|-----|-------------|:------:|
| **voice-typer** | Local push-to-talk voice dictation | ✓ (HUD) |
| [Clipboard](https://github.com/Slackadays/Clipboard) | Clipboard CLI | ✓ |
| [Flameshot](https://flameshot.org/) | Screenshots | ✓ |
| [worktrunk](https://github.com/) (`wt`) | Git-worktree workflow CLI | - |
| [opencode](https://opencode.ai/) | AI coding assistant — ships a full custom agent/skill framework (ticket → implement → PR review → merge); see `dot_config/opencode/` | ✓ |
| [gh](https://cli.github.com/) | GitHub CLI | - |
| [Obsidian](https://obsidian.md/) | Notes (per-vault) | ✓ |
| [Zen Browser](https://zen-browser.app/) | Firefox-based browser | - |

---

## Key Bindings

The essentials — press **`SUPER+K`** on the desktop for the full, searchable list.

### Hyprland (Linux) — `ALT` = window modifier, `SUPER` = apps
| Binding | Action |
|---------|--------|
| `ALT + Return` | Terminal (Herdr in Ghostty) |
| `ALT + Space` | App launcher (Walker) |
| `ALT + Shift + V` | Clipboard history |
| `SUPER + B / T / O / E` | Browser / Telegram / Obsidian / Files |
| `SUPER + K` | Keybindings cheatsheet |
| `ALT + C / X / V / A / Z` | Copy / Cut / Paste / Select-all / Undo (mac-style) |
| `ALT + Q` / `ALT + F` / `ALT + M` | Close / Fullscreen / Float |
| `ALT + ←↑↓→` | Move focus |
| `ALT + 1-0` / `ALT + Shift + 1-0` | Switch / move-to workspace |
| `Ctrl + Print` | Screenshot (Flameshot) |
| `SUPER + L` / `ALT + Ctrl + Q` | Lock / Power menu |
| `ALT + Shift + W` | Random wallpaper + theme |
| `F7` family | Voice dictation (see [Voice Dictation](#voice-dictation-voice-typer)) |
| both `Ctrl` keys | Toggle US / Arabic keyboard |

### macOS (AeroSpace)
| Binding | Action |
|---------|--------|
| `Cmd + Enter` / `Cmd + Shift + Enter` | Herdr (local) / remote Herdr |
| `Alt + B` / `Alt + O` | Zen Browser / Obsidian |
| `Cmd + arrows` / `Cmd + Shift + arrows` | Focus / move window |
| `Cmd + 1-9` / `Cmd + Shift + 1-9` | Switch / move-to workspace |
| `Cmd + F` / `Cmd + M` | Fullscreen / Float |
| `Cmd + Shift + W` | Random wallpaper + theme |
| `f7` family | Voice dictation (toggle-style) |

---

## Cross-Platform Architecture

### Platform Detection

```go
// .chezmoi.toml.tmpl
is_mac = true/false       // macOS
is_linux = true/false     // Linux
is_headless = true/false  // No GUI (VPS / SSH-only)
```

### What Gets Installed Where

| Component | macOS | Headless Linux | Arch Desktop |
|-----------|:-----:|:--------------:|:------------:|
| Shell (zsh, Starship, Atuin), NeoVim, TUI apps | ✓ | ✓ | ✓ |
| Theme system | ✓ | ✓ (TUI only) | ✓ |
| Ghostty / WezTerm | ✓ | - | ✓ |
| Hyprland desktop (Quickshell, Walker, swaync, greetd…) | - | - | ✓ |
| voice-typer | ✓ | - | ✓ |
| AeroSpace / SketchyBar / Borders | ✓ | - | - |
| Herdr (multiplexer) | ✓ | ✓ | ✓ |

### Target Systems

| System | Role | Status |
|--------|------|--------|
| **Arch Desktop** (Hyprland) | Primary daily driver | ✅ Active |
| **Mac** | Workstation | ✅ Active |
| **dev-hub** (Arch VPS, headless) | Remote dev | ✅ Active |
| **Windows** | TBD | 🔲 Planned |

---

## Customization

### User Preferences — `.chezmoidata/user.yaml`

```yaml
user:
  name: "Your Name"
  email: "your@email.com"

preferences:
  default_theme: "mocha"            # mocha, latte, frappe, macchiato
  toggle_themes: ["mocha", "latte"]
  wallpaper_folders:                # OS-aware
    linux:  { mocha: "~/Pictures/Wallpapers" }
    darwin: { mocha: "~/Pictures/Wallpapers" }

theme_sync:
  enabled: true
  devbox_host: "your-server"        # Tailscale hostname
```

### Adding a New App to the Theme System

1. Create `dot_config/theme-system/scripts/apps/myapp.py`:

```python
from .base import BaseApp

class MyAppTheme(BaseApp):
    requires_gui = False  # True if GUI-only

    def apply_theme(self, theme_data: dict) -> None:
        colors = theme_data["colors"]
        self.write_file(self.config_home / "myapp/theme.conf",
                        f'background = "{colors["base"]}"\n')
```

2. Register it in `apps/__init__.py`, and add the generated file to `.chezmoiignore.tmpl` if it's runtime-generated.

---

## Repository Structure

```
~/.local/share/chezmoi/
├── .chezmoi.toml.tmpl        # Platform detection & prompts
├── .chezmoidata/             # apps catalog + user preferences
├── .chezmoiignore.tmpl       # Platform-based file filtering
├── .chezmoiscripts/          # Installers + setup (packages, greetd, services…)
├── dot_config/
│   ├── hypr/                 # Hyprland desktop (native Lua)
│   ├── quickshell/           # Status bar, voice HUD, wallpaper picker
│   ├── walker/ swaync/ wlogout/   # Launcher, notifications, power menu
│   ├── voice-typer/          # Voice dictation daemon + client
│   ├── theme-system/         # Unified theming engine (34 app modules)
│   ├── opencode/             # AI agent/skill framework
│   ├── nvim/ ghostty/ herdr/ yazi/ …
│   └── aerospace/ sketchybar/     # macOS desktop
├── dot_zshrc.tmpl  dot_gitconfig.tmpl
├── private_dot_ssh/          # SSH config (Tailscale hosts + multiplexing)
└── private_Library/          # macOS LaunchAgents (incl. voice-typerd)
```

---

## macOS System Settings

Applied automatically via `run_onchange_after_macos-defaults.sh.tmpl`:

- **Dock / Menu Bar**: auto-hide
- **Finder**: path/status bars, extensions, folders first
- **Keyboard**: fast key repeat, full keyboard access
- **Screenshots**: `~/Pictures/Screenshots`, no shadows
- **Text Input**: smart quotes/dashes/autocorrect off
- **Key Remap**: Caps Lock ↔ Escape
- **Remote Login (SSH)**: enabled (for cross-machine clipboard)

---

## Acknowledgments

- [Hyprland](https://hyprland.org/), [Quickshell](https://quickshell.org/), [Walker](https://github.com/abenz1267/walker), [regreet](https://github.com/rharish101/ReGreet) — the Wayland desktop
- [Catppuccin](https://catppuccin.com/) + [matugen](https://github.com/InioX/matugen) — colors
- [Parakeet](https://github.com/lucataco/parakeet-cli) — on-device speech
- [chezmoi](https://chezmoi.io/) — dotfiles manager
- [LazyVim](https://www.lazyvim.org/) — NeoVim distribution

---

## License

MIT
