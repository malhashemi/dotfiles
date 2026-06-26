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

import fcntl
import json
import os
import subprocess
import sys
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
CONFIG_HOME = HOME / ".config"


def get_chezmoi_source() -> Path:
    """Get chezmoi source directory dynamically.

    Tries: 1) THEME_CHEZMOI_SOURCE override, 2) chezmoi source-path command,
    3) XDG_DATA_HOME, 4) default.
    """
    override = os.environ.get("THEME_CHEZMOI_SOURCE")
    if override:
        return Path(override).expanduser()

    try:
        result = subprocess.run(
            ["chezmoi", "source-path"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            source = Path(result.stdout.strip())
            if source.exists():
                return source
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback to XDG standard
    xdg_data = os.environ.get("XDG_DATA_HOME", HOME / ".local/share")
    return Path(xdg_data) / "chezmoi"


CHEZMOI_SOURCE = get_chezmoi_source()
CHEZMOI_CONFIG = CONFIG_HOME / "chezmoi/chezmoi.toml"
THEME_DATA = CHEZMOI_SOURCE / ".chezmoidata/theme.yaml"
WALLPAPER_DATA = CHEZMOI_SOURCE / ".chezmoidata/wallpaper-state.yaml"
THEMES_DIR = CHEZMOI_SOURCE / "dot_config/theme-system/themes"
LOCK_FILE = HOME / ".cache/theme-system-running"
APPLIED_GEN_FILE = HOME / ".cache/theme-system-applied-gen"
USER_DATA = CHEZMOI_SOURCE / ".chezmoidata/user.yaml"


def _read_applied_gen() -> str:
    """Wallpaper generation (last_updated) of the most recently applied theme."""
    try:
        return APPLIED_GEN_FILE.read_text().strip()
    except OSError:
        return ""


def _write_applied_gen(gen: str) -> None:
    try:
        APPLIED_GEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        APPLIED_GEN_FILE.write_text(gen)
    except OSError:
        pass


# Headless detection


def is_headless() -> bool:
    """Detect if running in a headless environment.

    Detection methods:
    1. Explicit environment variable: THEME_HEADLESS=1
    2. No DISPLAY on Linux (X11/Wayland not available)

    Returns:
        True if headless environment detected, False otherwise
    """
    # Explicit override via environment variable
    if os.environ.get("THEME_HEADLESS", "").lower() in ("1", "true", "yes"):
        return True

    # macOS always has GUI (even via SSH, we're configuring local machine)
    if sys.platform == "darwin":
        return False

    # Linux: Check for display (X11 or Wayland)
    if sys.platform == "linux":
        has_display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        if not has_display:
            return True

    return False


# State management utilities


def load_yaml(path: Path) -> dict:
    """Load YAML file"""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_chezmoi_config() -> dict:
    """Load chezmoi config (TOML) and return as nested dict"""
    if not CHEZMOI_CONFIG.exists():
        return {}
    try:
        import tomllib

        with open(CHEZMOI_CONFIG, "rb") as f:
            return tomllib.load(f)
    except ImportError:
        # Python < 3.11 fallback
        import tomlkit

        with open(CHEZMOI_CONFIG) as f:
            return tomlkit.load(f)


def save_yaml(path: Path, data: dict):
    """Save YAML file"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


def apply_theme_to_apps(theme_data: dict, *, wallpaper_only: bool = False) -> None:
    """Apply theme data to all registered apps.

    Respects headless mode - skips GUI apps on headless systems.

    Args:
        theme_data: Complete theme data dictionary with 'theme' key
        wallpaper_only: When True, only run apps that bake an asset from the
            wallpaper image (BaseApp.wallpaper_derived) — used to refresh the
            blurred backgrounds on a static-theme wallpaper change without
            re-running every color app.
    """
    apps = get_all_apps(CONFIG_HOME)
    headless = is_headless()
    platform_name = "linux" if sys.platform.startswith("linux") else sys.platform
    environment = "headless_linux" if platform_name == "linux" and headless else platform_name

    console.print(f"[dim]Theme environment: {environment}[/dim]")

    for app in apps:
        if not app.supports_current_platform():
            continue

        # Skip GUI apps on headless systems
        if headless and app.requires_gui:
            continue

        if wallpaper_only and not app.wallpaper_derived:
            continue
        app.apply_theme(theme_data)


def get_devbox_host() -> str | None:
    """Get devbox hostname from chezmoi config.

    Reads from tailscale_hosts.dev_hub in ~/.config/chezmoi/chezmoi.toml
    """
    config = load_chezmoi_config()
    return config.get("data", {}).get("tailscale_hosts", {}).get("dev_hub")


def push_to_devbox() -> bool:
    """Push theme.yaml to devbox and trigger apply.

    Returns:
        True if push succeeded, False otherwise
    """
    user_data = load_yaml(USER_DATA)
    sync_config = user_data.get("theme_sync", {})

    if not sync_config.get("enabled", False):
        console.print("[dim]Theme sync disabled[/dim]")
        return False

    devbox_host = get_devbox_host()
    if not devbox_host:
        console.print("[yellow]⚠ No tailscale_hosts.dev_hub in chezmoi config[/yellow]")
        console.print("[dim]Run 'chezmoi init' to configure[/dim]")
        return False

    # Remote path - same relative location in chezmoi source
    remote_theme_path = "~/.local/share/chezmoi/.chezmoidata/theme.yaml"
    remote_apply_cmd = "~/.config/theme-system/scripts/theme-manager.py apply"

    try:
        # Push theme.yaml via rsync
        console.print(f"[blue]📤 Pushing theme to {devbox_host}...[/blue]")
        subprocess.run(
            ["rsync", "-az", str(THEME_DATA), f"{devbox_host}:{remote_theme_path}"],
            timeout=15,
            capture_output=True,
            check=True,
        )

        # Trigger apply on remote
        console.print(f"[blue]🔄 Triggering apply on {devbox_host}...[/blue]")
        subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=5",
                "-o",
                "BatchMode=yes",
                devbox_host,
                remote_apply_cmd,
            ],
            timeout=60,
            capture_output=True,
            check=True,
        )

        console.print(f"[green]✓ Theme synced to {devbox_host}[/green]")
        return True

    except subprocess.TimeoutExpired:
        console.print(f"[yellow]⚠ Timeout connecting to {devbox_host}[/yellow]")
        return False
    except subprocess.CalledProcessError as e:
        console.print(f"[yellow]⚠ Failed to sync to {devbox_host}: {e}[/yellow]")
        return False
    except FileNotFoundError:
        console.print("[yellow]⚠ rsync or ssh not found[/yellow]")
        return False


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
    # Crash-safe, coalescing lock: rather than dropping a request when an apply
    # is already running (which left rapid wallpaper swaps out of sync with the
    # latest wallpaper), block until it finishes, then skip only if this exact
    # wallpaper generation was already applied by a concurrent run — so the most
    # recent swap always wins, with no redundant re-applies. flock auto-releases
    # on process exit, so a crashed apply never leaves a stale lock.
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_FILE, "w") as _lock:
        fcntl.flock(_lock, fcntl.LOCK_EX)

        gen = ""
        if theme_type == "dynamic":
            wp = load_yaml(WALLPAPER_DATA).get("wallpaper", {})
            cur_opacity = (
                opacity
                if opacity is not None
                else load_yaml(THEME_DATA).get("theme", {}).get("opacity", 0)
            )
            # Coalesce only true duplicates: the token covers everything that
            # changes the output (wallpaper, mode, opacity, contrast), so a
            # mode/opacity toggle on the same wallpaper is never wrongly skipped.
            gen = "|".join(
                str(x)
                for x in (
                    wp.get("last_updated", ""),
                    wp.get("current", ""),
                    detect_system_appearance(),
                    cur_opacity,
                    contrast,
                )
            )
            if _read_applied_gen() == gen:
                console.print("[dim]Already applied (no change) — skipping[/dim]")
                return

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
        apply_theme_to_apps(theme_data)

        console.print("[green]✅ Theme applied[/green]")

        # Auto-push to devbox if enabled
        user_data = load_yaml(USER_DATA)
        if user_data.get("theme_sync", {}).get("auto_push", False):
            push_to_devbox()

        # Record the applied wallpaper generation so concurrent rapid swaps
        # coalesce (a queued run sees its wallpaper is already applied).
        if gen:
            _write_applied_gen(gen)


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


@cli.command()
def apply():
    """Apply theme from existing state file (no color regeneration).

    Use this on devbox after theme.yaml has been synced from a source machine.
    Reads the current theme.yaml and applies to all apps, respecting headless mode.

    This command does NOT:
    - Regenerate colors from wallpaper
    - Require matugen or wallpaper access
    - Modify the theme.yaml file

    Examples:
        theme apply  # Apply whatever theme is in theme.yaml
    """
    theme_data = load_yaml(THEME_DATA)

    if not theme_data.get("theme"):
        raise click.ClickException(
            "No theme data found in theme.yaml. "
            "Run 'theme set' on a source machine and push, or run 'theme set' locally."
        )

    theme_name = theme_data["theme"].get("name", "unknown")
    theme_variant = theme_data["theme"].get("variant", "unknown")

    console.print(f"[blue]🎨 Applying theme: {theme_name} ({theme_variant})[/blue]")

    apply_theme_to_apps(theme_data)

    console.print("[green]✅ Theme applied from state[/green]")


@cli.command(name="refresh-backgrounds")
def refresh_backgrounds():
    """Re-render only the wallpaper-derived backgrounds (hyprlock, wlogout).

    Used by wallpaper-manager on a wallpaper change while a STATIC theme is
    active: the palette is fixed (colors need no regeneration), but those apps
    bake a blurred PNG from the wallpaper image which would otherwise go stale.
    Dynamic themes already refresh these as part of 'set dynamic'.

    Linux desktop only — the wallpaper-derived apps are linux GUI apps, so this
    is a no-op on macOS and on headless linux (the app filter skips them).
    """
    # Same crash-safe, coalescing lock as 'set': block on a concurrent apply,
    # then skip if this exact wallpaper was already rendered, so rapid swaps
    # converge on the latest with no redundant blur renders. The token is read
    # inside the lock so a queued run sees the final wallpaper state.
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_FILE, "w") as _lock:
        fcntl.flock(_lock, fcntl.LOCK_EX)

        wp = load_yaml(WALLPAPER_DATA).get("wallpaper", {})
        # "bg"-tagged token so it never collides with the 5-field dynamic gen
        # token that shares APPLIED_GEN_FILE.
        gen = "|".join(
            str(x) for x in ("bg", wp.get("last_updated", ""), wp.get("current", ""))
        )
        if _read_applied_gen() == gen:
            console.print("[dim]Backgrounds already current — skipping[/dim]")
            return

        theme_data = load_yaml(THEME_DATA)
        if not theme_data.get("theme"):
            raise click.ClickException("No theme data found in theme.yaml.")

        console.print("[blue]🖼️  Refreshing wallpaper backgrounds...[/blue]")
        apply_theme_to_apps(theme_data, wallpaper_only=True)
        console.print("[green]✅ Backgrounds refreshed[/green]")

        _write_applied_gen(gen)


@cli.command()
def push():
    """Push current theme to devbox.

    Sends theme.yaml to the configured devbox and triggers 'theme apply' there.
    Does NOT re-apply theme locally - just syncs to remote.

    Requirements:
    - theme_sync.enabled = true in .chezmoidata/user.yaml
    - tailscale_hosts.dev_hub configured via 'chezmoi init'

    Examples:
        theme push  # Push current theme to devbox
    """
    if not THEME_DATA.exists():
        raise click.ClickException(
            "No theme.yaml found. Run 'theme set' first to create a theme."
        )

    success = push_to_devbox()

    if not success:
        raise click.ClickException("Push failed. Check configuration and connectivity.")


if __name__ == "__main__":
    cli()
