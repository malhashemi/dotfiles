# Universal Theme System

A unified theming system for terminal applications on macOS, featuring Catppuccin themes with mauve accents.

## 🎨 Theme Variants

### Static Themes
1. **Catppuccin Mocha** - Warm dark theme with mauve accents (#cba6f7)
2. **Catppuccin Frappe** - Cool mid-tone dark with mauve accents (#ca9ee6)
3. **Catppuccin Macchiato** - Neutral dark with mauve accents (#c6a0f6)
4. **Catppuccin Latte** - Light theme with mauve accents (#8839ef)

### Dynamic Theme (Experimental)
5. **Dynamic** - Generates colors from wallpaper using `wallust`
   - Currently applies terminal escape sequences
   - WezTerm uses Mocha as fallback while displaying dynamic colors

## 📦 Currently Supported Applications

| Application | Hot Reload | Theme Support | Notes |
|------------|------------|---------------|-------|
| **WezTerm** | ✅ Yes | All 4 static + dynamic | Terminal emulator with all Catppuccin variants |
| **Atuin** | ✅ Yes | All 5 themes | Shell history - hot reload on new shell |
| **OpenCode** | ❌ No (restart required) | All 4 static themes | AI code editor |

## 🏗️ Current Architecture

```
~/.config/theme-system/
├── README.md                      # This file
├── config.yaml                    # Global configuration
├── theme-manager.py               # Main CLI tool (uses uv)
├── state/                         # Current state files
│   ├── current-theme.txt          # Active theme name
│   ├── wezterm-theme.txt          # WezTerm's theme
│   ├── wezterm-transparent.txt    # Transparency setting
│   └── current-wallpaper.txt      # Current wallpaper path
├── themes/                        # Theme definitions (JSON)
│   ├── catppuccin-mocha.json
│   ├── catppuccin-frappe.json
│   ├── catppuccin-macchiato.json
│   └── catppuccin-latte.json
├── scripts/                       # Helper scripts
│   ├── wallpaper-manager.sh      # Wallpaper & dynamic theme
│   └── setup-wezterm-themes.sh   # Setup script
├── cache/                         # Cache directory
│   ├── wallpaper.log
│   └── wallpaper-thumbs/
└── templates/                     # Reserved for future Jinja2 templates
```

## 🚀 Installation

### Prerequisites
```bash
# Install Python package manager (for theme-manager.py)
brew install uv

# Optional: For dynamic themes
brew install wallust
```

### Setup
The system is already installed if you have:
- `~/.config/theme-system/` directory with scripts
- Shell alias: `alias theme="~/.config/theme-system/theme-manager.py"`

Add to your `~/.zshrc`:
```bash
alias theme="~/.config/theme-system/theme-manager.py"
alias wallpaper="~/.config/theme-system/scripts/wallpaper-manager.sh"
```

Then reload: `source ~/.zshrc`

## 💻 Usage

### Basic Commands
```bash
# Set theme for all applications
theme set mocha
theme set frappe
theme set macchiato
theme set latte

# Toggle between mocha and latte
theme toggle

# Show current configuration
theme status

# Set theme with transparency (WezTerm only)
theme set mocha --transparency
theme set mocha -t
```

### Transparency Control
```bash
# Toggle transparency on/off
theme transparency

# Explicitly set transparency
theme transparency --on
theme transparency --off
```

### Wallpaper Management
```bash
# Set random wallpaper (from ~/Pictures/Wallpapers)
wallpaper random

# Set random wallpaper and generate dynamic theme
wallpaper random --theme

# Set specific wallpaper
wallpaper set /path/to/image.jpg

# Generate theme from current wallpaper
wallpaper theme

# Or use the theme command
theme dynamic
```

### Application-Specific Theming
```bash
# Theme specific applications only
theme set mocha --app wezterm
theme set latte --app atuin --app opencode
```

## 🔄 How Dynamic Theme Works

1. **Set Wallpaper**: Use `wallpaper random --theme`
2. **Color Extraction**: `wallust` analyzes wallpaper and generates colors
3. **Apply Colors**: 
   - Terminal colors updated via escape sequences
   - WezTerm uses Mocha as base + dynamic colors
   - State saved to `state/current-wallpaper.txt`

## 🎨 Color Structure

Each theme JSON contains:
```json
{
  "name": "Catppuccin Mocha",
  "variant": "dark",
  "colors": {
    "rosewater": "#f5e0dc",
    "mauve": "#cba6f7",
    "text": "#cdd6f4",
    "base": "#1e1e2e",
    // ... all Catppuccin colors
  },
  "semantic": {
    "primary": "mauve",
    "accent": "mauve",
    "background": "base",
    // ... semantic color mappings
  }
}
```

## 🔧 Configuration

Edit `~/.config/theme-system/config.yaml`:
```yaml
default_theme: mocha
transparency: false

apps:
  wezterm:
    enabled: true
    transparency: false
    font_size: 16.0
    
  atuin:
    enabled: true
    
  opencode:
    enabled: true
```

## 📁 State Management

All state is stored in `~/.config/theme-system/state/`:
- `current-theme.txt` - Active theme (mocha/frappe/macchiato/latte/dynamic)
- `wezterm-theme.txt` - WezTerm's theme name
- `wezterm-transparent.txt` - Transparency (true/false)
- `current-wallpaper.txt` - Path to current wallpaper

## 🗺️ Roadmap

Planned features (not yet implemented):

### Phase 1: Core Enhancements
- [ ] Proper dynamic theme implementation in WezTerm (parse wallust colors)
- [ ] Jinja2 templates for config generation
- [ ] Export/import theme configurations

### Phase 2: Application Support
- [ ] Starship (shell prompt)
- [ ] Neovim (text editor)
- [ ] btop (system monitor)
- [ ] Aerospace (window manager borders)
- [ ] SketchyBar (status bar)

### Phase 3: Advanced Features
- [ ] Material You color generation with matugen
- [ ] Automatic wallpaper change detection (FSEvents)
- [ ] Per-app theme overrides
- [ ] Theme scheduling (light during day, dark at night)
- [ ] Theme preview before applying

## 🐛 Known Issues

- **OpenCode**: Requires restart for theme changes to apply
- **Dynamic theme**: WezTerm shows colors via escape sequences but uses Mocha as config fallback
- **Wallust**: Requires manual installation (`brew install wallust`)
- **First run**: May need to reload shell after applying theme

## 📝 Development

### Adding New Application Support

To add a new application:

1. Add theme files to app's config directory (e.g., `~/.config/atuin/themes/`)
2. Add `apply_<appname>()` method to `theme-manager.py`
3. Update `apply_all()` method to include new app
4. Update this README

### Theme File Structure

Create theme JSON in `themes/` directory following Catppuccin structure.
See existing files for examples.

## 🤝 Contributing

This is a personal dotfiles project. Feel free to fork and adapt for your own setup!

## 📄 License

Personal use - MIT License