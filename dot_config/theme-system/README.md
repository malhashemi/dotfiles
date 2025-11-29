# Theme System

A unified theming engine that synchronizes colors across 21 applications. Change your wallpaper and watch everything update.

## Features

- **21 apps synchronized** to one color scheme
- **Two theme modes**: Static (Catppuccin) or Dynamic (wallpaper-based)
- **Cross-platform**: macOS, Linux (Hyprland), headless servers
- **Cross-machine sync**: Push themes from GUI machine to headless servers
- **Plugin architecture**: Easy to add new apps

## Installation

### Dependencies

```bash
# matugen - Material Design 3 color extraction (for dynamic themes)
cargo install --locked matugen

# Python dependencies are handled automatically via uv
# (inline script dependencies in theme-manager.py)
```

### Verify Installation

```bash
theme status
```

## Usage

### Basic Commands

```bash
# Show current theme state
theme status

# Static themes (Catppuccin)
theme set static                    # Auto-detect light/dark from system
theme set static --variant mocha    # Force specific variant (mocha/latte/frappe/macchiato)
theme set static -o 85              # With 85% opacity

# Dynamic themes (from wallpaper)
theme set dynamic                   # Extract colors from current wallpaper
theme set dynamic -c 0.2            # With +0.2 contrast adjustment

# Adjust opacity (0-100)
theme opacity 85

# Switch system appearance
theme mode dark
theme mode light
```

### Wallpaper Management

```bash
# Set wallpaper and auto-apply dynamic theme
wallpaper set ~/Pictures/wallpaper.jpg

# Random wallpaper from configured directory
wallpaper random

# Just set wallpaper without theme change
wallpaper set ~/Pictures/wallpaper.jpg --no-theme
```

### Cross-Machine Sync

Sync your theme from a GUI machine (macOS) to headless servers:

```bash
# On GUI machine: Push current theme to remote
theme push

# On headless machine: Apply received theme
theme apply
```

Configure remote host in `~/.local/share/chezmoi/.chezmoidata/user.yaml`:

```yaml
theme_sync:
  enabled: true
  devbox_host: "your-server"  # Tailscale hostname
```

## Theme Modes

| Mode | Source | Best For |
|------|--------|----------|
| **Static** | Catppuccin JSON files | Consistent, predictable colors |
| **Dynamic** | Wallpaper via matugen | Matching desktop aesthetic |

### Static Theme Variants

- `mocha` - Dark, warm
- `macchiato` - Dark, medium
- `frappe` - Dark, cool
- `latte` - Light

### Dynamic Theme

Uses [matugen](https://github.com/InioX/matugen) to extract Material Design 3 colors from your wallpaper:

```
Wallpaper ──► matugen ──► Material Design 3 colors ──► 21 apps
```

## Supported Applications

### Terminals
| App | GUI Required | Notes |
|-----|:------------:|-------|
| WezTerm | ✓ | External color file |
| Ghostty | ✓ | External color file |

### Editors
| App | GUI Required | Notes |
|-----|:------------:|-------|
| NeoVim | | Lua colorscheme |
| Zed | ✓ | JSON theme |

### macOS Desktop
| App | GUI Required | Notes |
|-----|:------------:|-------|
| SketchyBar | ✓ | Shell variables |
| Borders | ✓ | bordersrc |

### TUI Applications
| App | GUI Required | Notes |
|-----|:------------:|-------|
| Starship | | Inline TOML palette |
| Atuin | | TOML theme |
| lazygit | | YAML theme |
| gitui | | RON theme |
| yazi | | Flavor directory |
| btop | | Theme file |
| bottom | | TOML theme |
| Television | | TOML theme |
| ncspot | | Inline config |
| CAVA | | Config file |
| glow | | JSON theme |
| Posting | | YAML theme |

### Other
| App | GUI Required | Notes |
|-----|:------------:|-------|
| OpenCode | | JSON theme |
| Flameshot | ✓ | INI config |
| Obsidian | ✓ | Per-vault CSS |

## Architecture

```
theme-system/
├── scripts/
│   ├── executable_theme-manager.py    # Main CLI
│   ├── executable_wallpaper-manager.py
│   ├── apps/                          # App plugins
│   │   ├── __init__.py                # Registry
│   │   ├── base.py                    # BaseApp class
│   │   ├── wezterm.py
│   │   ├── nvim.py
│   │   └── ... (21 apps)
│   └── utils/
│       ├── system.py                  # System appearance
│       ├── colors.py                  # Color utilities
│       ├── color_math.py              # Color math
│       └── hue_generator.py           # Hue palettes
└── themes/
    ├── catppuccin-mocha.json
    ├── catppuccin-latte.json
    ├── catppuccin-frappe.json
    └── catppuccin-macchiato.json
```

### BaseApp Pattern

All app plugins inherit from `BaseApp`:

```python
from .base import BaseApp

class MyAppTheme(BaseApp):
    # Set True if app requires GUI (skipped on headless)
    requires_gui = False
    
    def __init__(self, config_home: Path):
        super().__init__("MyApp", config_home)
    
    def apply_theme(self, theme_data: dict) -> None:
        colors = theme_data["colors"]      # Catppuccin colors
        material = theme_data["material"]  # Material Design 3 colors
        opacity = theme_data["opacity"]    # 0-100
        
        # Generate config
        content = f'background = "{colors["base"]}"\n'
        self.write_file(self.config_home / "myapp/theme.conf", content)
        
        # Optionally reload app
        self.run_command(["myapp", "reload"])
```

### Theme Data Structure

```python
theme_data = {
    "name": "mocha",           # or "dynamic"
    "variant": "dark",         # light/dark/amoled
    "opacity": 85,             # 0-100
    "colors": {                # Catppuccin palette
        "base": "#1e1e2e",
        "mantle": "#181825",
        "crust": "#11111b",
        "text": "#cdd6f4",
        "subtext0": "#a6adc8",
        # ... all Catppuccin colors
    },
    "material": {              # Material Design 3 (all themes)
        "primary": "#cba6f7",
        "on_primary": "#1e1e2e",
        "secondary": "#f5c2e7",
        # ... all MD3 colors
    }
}
```

## Adding a New App

1. **Create the plugin** at `scripts/apps/myapp.py`:

```python
from pathlib import Path
from .base import BaseApp

class MyAppTheme(BaseApp):
    requires_gui = False  # Set True for GUI-only apps
    
    def __init__(self, config_home: Path):
        super().__init__("MyApp", config_home)
    
    def apply_theme(self, theme_data: dict) -> None:
        colors = theme_data["colors"]
        
        content = f'''# MyApp Theme - Auto-generated
background = "{colors["base"]}"
foreground = "{colors["text"]}"
accent = "{colors["mauve"]}"
'''
        self.write_file(self.config_home / "myapp/colors.conf", content)
```

2. **Register in `apps/__init__.py`**:

```python
from .myapp import MyAppTheme

def get_all_apps(config_home: Path) -> list:
    return [
        # ... existing apps
        MyAppTheme(config_home),
    ]
```

3. **Add to `.chezmoiignore.tmpl`** if the theme file is runtime-generated:

```
# MyApp (external file method)
.config/myapp/colors.conf
```

## Platform Support

| Platform | System Appearance | Dynamic Themes | Notes |
|----------|:-----------------:|:--------------:|-------|
| macOS | ✓ | ✓ | Full support |
| Linux (Hyprland) | ✓ | ✓ | Via gsettings |
| Linux (Headless) | - | - | TUI apps only |
| Windows | ✓ | ✓ | Planned |
| Termux | - | - | TUI apps only |

### Headless Detection

Apps with `requires_gui = True` are automatically skipped on headless systems. Detection methods:

1. `THEME_HEADLESS=1` environment variable (explicit)
2. No `DISPLAY` or `WAYLAND_DISPLAY` on Linux

## Troubleshooting

### matugen not found

```bash
cargo install --locked matugen
# Ensure ~/.cargo/bin is in PATH
```

### Theme not applying to specific app

1. Check if app has `requires_gui = True` and you're on headless
2. Check app's config path matches what the plugin expects
3. Run `theme set static -v` for verbose output

### Colors look wrong in dynamic mode

Try adjusting contrast:

```bash
theme set dynamic -c 0.3   # Increase contrast
theme set dynamic -c -0.2  # Decrease contrast
```

## License

MIT
