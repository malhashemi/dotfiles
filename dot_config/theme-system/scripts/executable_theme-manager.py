#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.0", "pyyaml>=6.0", "rich>=13.0", "tomlkit>=0.12.0", "pynvim>=0.5.0"]
# ///

"""Universal Theme Manager - Modular Architecture

Simplified commands:
- theme set static [--variant VARIANT] [-o OPACITY]
- theme set dynamic [-o OPACITY] [-c CONTRAST]
- theme opacity <0-100>
- theme mode <light|dark>
- theme status
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import click
import yaml
from rich.console import Console

# Import modular components
from apps import get_all_apps
from utils import (
    detect_system_appearance,
    set_system_appearance,
    extract_colors_matugen,
    map_catppuccin_to_material,
)

console = Console()

# Paths
HOME = Path.home()
CHEZMOI_SOURCE = HOME / ".local/share/chezmoi"
CONFIG_HOME = HOME / ".config"
THEME_DATA = CHEZMOI_SOURCE / ".chezmoidata/theme.yaml"
WALLPAPER_DATA = CHEZMOI_SOURCE / ".chezmoidata/wallpaper-state.yaml"
THEMES_DIR = CHEZMOI_SOURCE / "dot_config/theme-system/themes"
LOCK_FILE = HOME / ".cache/theme-system-running"


# State management utilities

def load_yaml(path: Path) -> dict:
    """Load YAML file"""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: dict):
    """Save YAML file"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


# Theme data builders

def build_static_theme_data(variant: str, opacity: int) -> dict:
    """Build theme data for static Catppuccin theme
    
    Args:
        variant: Catppuccin variant (mocha, latte, frappe, macchiato)
        opacity: Opacity percentage (0-100)
        
    Returns:
        Complete theme data dictionary
    """
    console.print(f"[blue]🎨 Theme: {variant}[/blue]")
    
    # Load Catppuccin theme
    theme_file = THEMES_DIR / f"catppuccin-{variant}.json"
    if not theme_file.exists():
        raise click.ClickException(f"Theme file not found: {theme_file}")
    
    with open(theme_file) as f:
        theme_json = json.load(f)
    
    ctp = theme_json["colors"]
    material_colors = map_catppuccin_to_material(ctp)
    
    return {
        "theme": {
            "name": variant,
            "variant": theme_json.get("variant", "dark"),
            "opacity": opacity,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "colors": ctp,
            "material": material_colors,
        }
    }


def build_dynamic_theme_data(
    wallpaper_path: str,
    mode: str,
    opacity: int,
    contrast: float
) -> dict:
    """Build theme data for dynamic Material You theme
    
    Args:
        wallpaper_path: Path to wallpaper image
        mode: Color mode (light, dark, amoled)
        opacity: Opacity percentage (0-100)
        contrast: Contrast adjustment (-1.0 to 1.0)
        
    Returns:
        Complete theme data dictionary
    """
    console.print(f"[blue]🌈 Dynamic theme ({mode} mode, contrast: {contrast:+.1f})...[/blue]")
    
    material_colors = extract_colors_matugen(
        Path(wallpaper_path),
        mode=mode,
        contrast=contrast
    )
    
    return {
        "theme": {
            "name": "dynamic",
            "variant": mode,
            "opacity": opacity,
            "contrast": contrast,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "material": material_colors,
            "source_wallpaper": str(wallpaper_path),
        }
    }


# Neovim Configuration Generators

def blend_hex_colors(fg: str, bg: str, alpha: float) -> str:
    """Blend foreground color with background at given alpha (0.0-1.0)"""
    fg_rgb = tuple(int(fg.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    bg_rgb = tuple(int(bg.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    blended = tuple(
        int(fg_rgb[i] * alpha + bg_rgb[i] * (1 - alpha))
        for i in range(3)
    )
    
    return f"#{blended[0]:02x}{blended[1]:02x}{blended[2]:02x}"


def generate_nvim_colors(theme_data: dict):
    """Generate colors-nvim.lua for Neovim from theme data
    
    For static themes: Returns empty dict (use builtin Catppuccin)
    For dynamic theme: Returns full MD3 palette with 8 distinct hues
    """
    from utils.hue_generator import generate_ide_palette, generate_semantic_ansi, validate_hue_distribution
    
    theme = theme_data.get('theme', {})
    theme_name = theme.get('name', 'mocha')
    variant = theme.get('variant', 'dark')
    
    console.print("[blue]🎨 Generating Neovim colors...[/blue]")
    
    if theme_name == 'dynamic':
        # Use Material Design 3 colors - generate 8 distinct hues
        mat = theme.get('material', {})
        
        # Get base colors
        base_bg = mat.get('surface', '#1C1B1F')
        base_text = mat.get('on_surface', '#E6E1E5')
        
        # Generate 8-hue palette with proper contrast
        palette = generate_ide_palette(mat, variant, base_bg, base_text)
        
        # Generate semantic ANSI colors
        ansi = generate_semantic_ansi(palette)
        
        # Validate hue distribution
        validation = validate_hue_distribution(palette)
        if not validation['is_valid']:
            console.print(f"[yellow]⚠ Warning: Hue distribution may not be optimal[/yellow]")
            if validation['duplicates']:
                console.print(f"[yellow]  Duplicate hues found: {len(validation['duplicates'])}[/yellow]")
        else:
            console.print(f"[green]✓ Validated 8 distinct hue families[/green]")
        
        # Format hue comments for documentation
        hue_comments = []
        for i, (name, h, s, l) in enumerate(validation['hues']):
            hue_comments.append(f"  {name:12} = {palette[name]:8}  -- H:{h:6.1f}° S:{s:5.1f}% L:{l:5.1f}%")
        
        # Format as Lua table for Neovim
        lua_content = f"""-- Neovim Colors - Dynamic theme (Material Design 3)
-- Generated by theme-manager.py
-- Do not edit manually - changes will be overwritten
-- Variant: {variant}

local M = {{
  -- Base colors
  base = "{palette['base']}",
  mantle = "{palette['mantle']}",
  crust = "{palette['crust']}",
  
  -- Text hierarchy (WCAG AAA compliant)
  text = "{palette['text']}",
  subtext1 = "{palette['subtext1']}",
  subtext0 = "{palette['subtext0']}",
  
  -- Surface variants
  surface0 = "{palette['surface0']}",
  surface1 = "{palette['surface1']}",
  surface2 = "{palette['surface2']}",
  
  -- Overlays and borders
  overlay0 = "{palette['overlay0']}",
  overlay1 = "{palette['overlay1']}",
  overlay2 = "{palette['overlay2']}",
  
  -- 8 distinct hue families for IDE syntax
  red = "{palette['red']}",          
  maroon = "{palette['maroon']}",
  peach = "{palette['peach']}",      
  yellow = "{palette['yellow']}",    
  green = "{palette['green']}",      
  teal = "{palette['teal']}",
  sky = "{palette['sky']}",          
  sapphire = "{palette['sapphire']}",
  blue = "{palette['blue']}",        
  lavender = "{palette['lavender']}",
  mauve = "{palette['mauve']}",      
  pink = "{palette['pink']}",        
  flamingo = "{palette['flamingo']}",
  rosewater = "{palette['rosewater']}",
}}

-- Semantic ANSI colors (for terminal emulators)
M.ansi = {{
  -- Normal (ANSI 0-7)
  black = "{ansi['ansi_black']}",
  red = "{ansi['ansi_red']}",
  green = "{ansi['ansi_green']}",        -- Actual green!
  yellow = "{ansi['ansi_yellow']}",      -- Actual yellow!
  blue = "{ansi['ansi_blue']}",          -- Actual blue!
  magenta = "{ansi['ansi_magenta']}",
  cyan = "{ansi['ansi_cyan']}",
  white = "{ansi['ansi_white']}",
  
  -- Bright (ANSI 8-15)
  bright_black = "{ansi['ansi_bright_black']}",
  bright_red = "{ansi['ansi_bright_red']}",
  bright_green = "{ansi['ansi_bright_green']}",
  bright_yellow = "{ansi['ansi_bright_yellow']}",
  bright_blue = "{ansi['ansi_bright_blue']}",
  bright_magenta = "{ansi['ansi_bright_magenta']}",
  bright_cyan = "{ansi['ansi_bright_cyan']}",
  bright_white = "{ansi['ansi_bright_white']}",
}}

return M
"""
    else:
        # Static theme: Return empty (use builtin Catppuccin)
        lua_content = f"""-- Neovim Colors - Static Catppuccin {theme_name}
-- Generated by theme-manager.py
-- For static themes, use builtin Catppuccin plugin (no overrides needed)

return {{}}
"""
    
    # Write to ~/.config/nvim/lua/themes/colors-nvim.lua
    nvim_colors = CONFIG_HOME / "nvim/lua/themes/colors-nvim.lua"
    nvim_colors.parent.mkdir(parents=True, exist_ok=True)
    with open(nvim_colors, 'w') as f:
        f.write(lua_content)
    
    console.print(f"[green]✓ Generated {nvim_colors}[/green]")
    
    # Also generate theme-state.lua to persist theme choice across restarts
    state_content = f"""-- Neovim Theme State
-- Generated by theme-manager.py
-- This file tells Neovim which theme to load on startup

return {{
  theme_name = "{theme_name}",
  is_dynamic = {str(theme_name == 'dynamic').lower()},
}}
"""
    
    theme_state = CONFIG_HOME / "nvim/lua/themes/theme-state.lua"
    with open(theme_state, 'w') as f:
        f.write(state_content)
    
    console.print(f"[green]✓ Generated {theme_state}[/green]")


def generate_nvim_opacity_data(theme_data: dict):
    """Generate opacity-data.lua with just the values
    
    This is pure data, logic is in opacity-manager.lua
    """
    theme = theme_data.get('theme', {})
    opacity_percent = theme.get('opacity', 0)
    opacity_float = opacity_percent / 100.0
    
    console.print(f"[blue]🔍 Generating Neovim opacity data ({opacity_percent}%)...[/blue]")
    
    lua_content = f"""-- Opacity Data
-- Generated by theme-manager.py
-- Used by opacity-manager.lua to apply opacity settings

return {{
  opacity = {opacity_float},
  opacity_percent = {opacity_percent},
}}
"""
    
    # Write to ~/.config/nvim/lua/config/opacity-data.lua
    opacity_data = CONFIG_HOME / "nvim/lua/config/opacity-data.lua"
    opacity_data.parent.mkdir(parents=True, exist_ok=True)
    
    with open(opacity_data, 'w') as f:
        f.write(lua_content)
    
    console.print(f"[green]✓ Generated {opacity_data}[/green]")


# CLI Commands

@click.group()
def cli():
    """Universal Theme Manager"""
    pass


@cli.command()
@click.argument("theme_type", type=click.Choice(["static", "dynamic"]))
@click.option("-o", "--opacity", type=click.IntRange(0, 100), default=None, help="Opacity (0=invisible, 100=solid)")
@click.option("--variant", type=click.Choice(["mocha", "latte", "frappe", "macchiato"]), default=None, help="Static theme variant")
@click.option("-c", "--contrast", type=click.FloatRange(-1.0, 1.0), default=0.0, help="Contrast adjustment for dynamic theme")
def set(theme_type: str, opacity: int | None, variant: str | None, contrast: float):
    """Set theme (static or dynamic)
    
    Examples:
        theme set static              # Auto-detect mocha/latte from system
        theme set static --variant frappe
        theme set static -o 65        # With 65% opacity
        theme set dynamic             # Use current wallpaper
        theme set dynamic -c 0.5      # High contrast dynamic theme
    """
    # Lock to prevent concurrent runs
    if LOCK_FILE.exists():
        raise click.ClickException("Theme manager already running")
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCK_FILE.touch()
    
    try:
        theme_data = load_yaml(THEME_DATA)
        
        # Preserve current opacity if not specified
        if opacity is None:
            opacity = theme_data.get("theme", {}).get("opacity", 0)
        
        if theme_type == "static":
            # Auto-detect variant based on system appearance if not specified
            if variant is None:
                system_mode = detect_system_appearance()
                variant = "latte" if system_mode == "light" else "mocha"
                console.print(f"[dim]Auto-detected variant: {variant} (system is {system_mode})[/dim]")
            
            theme_data = build_static_theme_data(variant, opacity)
            
        else:  # dynamic
            # Get wallpaper path
            wallpaper_state = load_yaml(WALLPAPER_DATA)
            wallpaper_path = wallpaper_state.get("wallpaper", {}).get("current")
            
            if not wallpaper_path or not Path(wallpaper_path).exists():
                raise click.ClickException(
                    "No wallpaper set. Run 'wallpaper set <path>' first."
                )
            
            # Auto-detect mode from system appearance
            mode = detect_system_appearance()
            console.print(f"[dim]Auto-detected mode: {mode}[/dim]")
            
            theme_data = build_dynamic_theme_data(wallpaper_path, mode, opacity, contrast)
        
        # Save state
        save_yaml(THEME_DATA, theme_data)
        console.print("[green]✓ Theme state saved[/green]")
        
        # Apply to all registered apps
        apps = get_all_apps(CONFIG_HOME)
        for app in apps:
            app.apply_theme(theme_data)
        
        # Generate Neovim config files
        generate_nvim_colors(theme_data)
        generate_nvim_opacity_data(theme_data)
        
        # NeoVim will auto-reload via file watcher when window regains focus
        console.print("[dim]  NeoVim will auto-reload when you switch back[/dim]")
        console.print(f"[green]✅ Theme applied[/green]")
        
    finally:
        LOCK_FILE.unlink(missing_ok=True)


@cli.command()
@click.argument("value", type=click.IntRange(0, 100))
def opacity(value: int):
    """Change opacity without changing theme (0=invisible, 100=solid)
    
    Example:
        theme opacity 65    # Set 65% opacity
    """
    theme_data = load_yaml(THEME_DATA)
    current_theme = theme_data.get("theme", {})
    theme_name = current_theme.get("name", "mocha")
    
    console.print(f"[blue]🔲 Setting opacity to {value}%...[/blue]")
    
    # Determine if static or dynamic
    if theme_name == "dynamic":
        # Re-apply dynamic theme with new opacity
        current_mode = current_theme.get("variant", "dark")
        current_contrast = current_theme.get("contrast", 0.0)
        
        ctx = click.Context(set)
        ctx.invoke(
            set,
            theme_type="dynamic",
            opacity=value,
            variant=None,
            contrast=current_contrast,
        )
    else:
        # Re-apply static theme with new opacity
        ctx = click.Context(set)
        ctx.invoke(
            set,
            theme_type="static",
            opacity=value,
            variant=theme_name,
            contrast=0.0,
        )


@cli.command()
@click.argument("mode", type=click.Choice(["light", "dark"]))
def mode(mode: str):
    """Switch light/dark mode (sets system appearance + updates theme)
    
    Behavior:
    - Always sets macOS system appearance
    - Static theme: Switches mocha ↔ latte
    - Dynamic theme: Regenerates with new mode
    
    Examples:
        theme mode dark     # Dark system + mocha (or dynamic dark)
        theme mode light    # Light system + latte (or dynamic light)
    """
    # Set system appearance
    console.print(f"[blue]🌓 Setting system to {mode} mode...[/blue]")
    success = set_system_appearance(mode)
    
    if not success:
        console.print("[red]✗ Failed to set system appearance[/red]")
        return
    
    console.print(f"[green]✓ macOS appearance set to {mode}[/green]")
    
    # Update theme based on current type
    theme_data = load_yaml(THEME_DATA)
    current_theme = theme_data.get("theme", {})
    current_type = current_theme.get("name")
    current_opacity = current_theme.get("opacity", 0)
    
    if current_type == "dynamic":
        # Regenerate dynamic theme with new mode
        current_contrast = current_theme.get("contrast", 0.0)
        console.print(f"[blue]🔄 Regenerating dynamic theme for {mode} mode...[/blue]")
        
        ctx = click.Context(set)
        ctx.invoke(
            set,
            theme_type="dynamic",
            opacity=current_opacity,
            variant=None,
            contrast=current_contrast,
        )
    else:
        # Switch static theme variant
        new_variant = "latte" if mode == "light" else "mocha"
        console.print(f"[blue]🎨 Switching to {new_variant}...[/blue]")
        
        ctx = click.Context(set)
        ctx.invoke(
            set,
            theme_type="static",
            opacity=current_opacity,
            variant=new_variant,
            contrast=0.0,
        )


@cli.command()
def status():
    """Show current theme status"""
    theme_data = load_yaml(THEME_DATA)
    theme = theme_data.get("theme", {})
    opacity = theme.get("opacity", 0)
    
    console.print(f"\n[bold]🎨 Current Theme[/bold]")
    console.print(f"  Name: {theme.get('name', 'none')}")
    console.print(f"  Variant: {theme.get('variant', 'unknown')}")
    console.print(f"  Opacity: {opacity}% (0=invisible, 100=solid)")
    
    # Show additional info for dynamic themes
    if theme.get("name") == "dynamic":
        contrast = theme.get("contrast", 0.0)
        console.print(f"  Contrast: {contrast:+.1f} (-1 to +1)")
        if "source_wallpaper" in theme:
            wallpaper = Path(theme["source_wallpaper"]).name
            console.print(f"  Wallpaper: {wallpaper}")
    
    # Show system appearance
    system_mode = detect_system_appearance()
    console.print(f"  System: {system_mode} mode")
    console.print()


if __name__ == "__main__":
    cli()
