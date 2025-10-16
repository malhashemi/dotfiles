# Theme System Architecture

## Design Principle: Fast & Surgical

The theme system generates config files **directly**, not through `chezmoi apply`.

## Why Not `chezmoi apply` for Theme Changes?

### ❌ Problems with `chezmoi apply`:
- **Heavyweight**: Regenerates ALL template files
- **Slow**: Unnecessary overhead (~2-3 seconds)
- **Side effects**: Could overwrite manually tweaked files
- **Wrong use case**: chezmoi is for dotfile management, not runtime config

### ✅ Current Architecture:
```
theme set mocha
  ↓
1. Update .chezmoidata/theme.yaml (state tracking)
  ↓
2. Generate ~/.config/wezterm/colors-wezterm.lua DIRECTLY
  ↓
3. WezTerm auto-reloads (< 1 second)
```

## When to Use `chezmoi apply`

Use `chezmoi apply` for:
- ✅ Initial setup on new machine
- ✅ Bootstrapping entire dotfiles
- ✅ Updating non-theme configs
- ❌ NOT for daily theme switching

## File Generation Flow

### Static Themes (mocha, latte, frappe, macchiato)
```
theme set mocha
  ↓
theme-manager.py:
  1. Load catppuccin-mocha.json
  2. Save to theme.yaml (state)
  3. generate_wezterm_colors() → writes Lua directly
  4. sleep(2) for WezTerm pickup
```

### Dynamic Theme (from wallpaper)
```
wallpaper set image.jpg → Sets macOS/Linux wallpaper
                         → Saves to wallpaper-state.yaml
                         → If dynamic theme: triggers theme-manager.py

theme set dynamic
  ↓
theme-manager.py:
  1. Run matugen on wallpaper
  2. Extract Material Design 3 colors
  3. Save to theme.yaml (state)
  4. generate_wezterm_colors() → writes Lua directly
  5. sleep(2) for WezTerm pickup
```

## State Files (for Reproducibility)

State is tracked in `.chezmoidata/` so `chezmoi apply` can reproduce your setup:

- **`.chezmoidata/theme.yaml`**: Current theme, colors, transparency
- **`.chezmoidata/wallpaper-state.yaml`**: Current wallpaper path
- **`.chezmoidata/user.yaml`**: User preferences (font, defaults)

When you run `chezmoi apply` on a new machine, these files ensure your exact theme setup is restored.

## Adding New Applications

To add theme support for a new app:

1. **Create color file template** (if app needs one):
   ```
   dot_config/myapp/colors-myapp.lua.tmpl
   ```

2. **Add generation function** to `theme-manager.py`:
   ```python
   def generate_myapp_colors(theme_data: dict):
       # Generate colors file for myapp
       pass
   ```

3. **Call in `set()` command**:
   ```python
   generate_wezterm_colors(theme_data)
   generate_myapp_colors(theme_data)  # Add this
   ```

## Performance

- **Static theme switch**: < 1 second
- **Dynamic theme (with matugen)**: 2-3 seconds
- **`chezmoi apply` (full)**: 3-5 seconds (not used for themes)

## Summary

**Single Source of Truth**: `colors-wezterm.lua` is always generated directly
**Fast**: No chezmoi overhead
**State Tracked**: `.chezmoidata/` ensures reproducibility
**Surgical**: Only colors change, nothing else touched
