#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.0", "pyyaml>=6.0", "rich>=13.0", "tomlkit>=0.12.0", "pynvim>=0.5.0", "ruamel.yaml>=0.18.0"]
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
    wallpaper_path: str, mode: str, opacity: int, contrast: float
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
    console.print(
        f"[blue]🌈 Dynamic theme ({mode} mode, contrast: {contrast:+.1f})...[/blue]"
    )

    material_colors = extract_colors_matugen(
        Path(wallpaper_path), mode=mode, contrast=contrast
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


# CLI Commands


@click.group()
def cli():
    """Universal Theme Manager"""
    pass


@cli.command()
@click.argument("theme_type", type=click.Choice(["static", "dynamic"]))
@click.option(
    "-o",
    "--opacity",
    type=click.IntRange(0, 100),
    default=None,
    help="Opacity (0=invisible, 100=solid)",
)
@click.option(
    "--variant",
    type=click.Choice(["mocha", "latte", "frappe", "macchiato"]),
    default=None,
    help="Static theme variant",
)
@click.option(
    "-c",
    "--contrast",
    type=click.FloatRange(-1.0, 1.0),
    default=0.0,
    help="Contrast adjustment for dynamic theme",
)
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
                console.print(
                    f"[dim]Auto-detected variant: {variant} (system is {system_mode})[/dim]"
                )

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

            theme_data = build_dynamic_theme_data(
                wallpaper_path, mode, opacity, contrast
            )

        # Save state
        save_yaml(THEME_DATA, theme_data)
        console.print("[green]✓ Theme state saved[/green]")

        # Apply to all registered apps
        apps = get_all_apps(CONFIG_HOME)
        for app in apps:
            app.apply_theme(theme_data)

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
