#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.0", "pyyaml>=6.0", "rich>=13.0"]
# ///

"""Universal Wallpaper Manager"""

import json
import random as random_module
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import click
import yaml
from rich.console import Console

console = Console()

HOME = Path.home()
CONFIG_HOME = HOME / ".config"


def get_chezmoi_source() -> Path:
    """Get chezmoi source directory dynamically."""
    try:
        result = subprocess.run(
            ["chezmoi", "source-path"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    import os

    xdg_data = os.environ.get("XDG_DATA_HOME", HOME / ".local/share")
    return Path(xdg_data) / "chezmoi"


CHEZMOI_SOURCE = get_chezmoi_source()
THEME_DATA = CHEZMOI_SOURCE / ".chezmoidata/theme.yaml"
USER_DATA = CHEZMOI_SOURCE / ".chezmoidata/user.yaml"
WALLPAPER_DATA = CHEZMOI_SOURCE / ".chezmoidata/wallpaper-state.yaml"
THEME_MANAGER = CONFIG_HOME / "theme-system/scripts/theme-manager.py"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def resolve_wallpaper_folder(theme_name: str) -> Path | None:
    """Resolve the wallpaper folder for a theme, OS-aware.

    user.yaml schema (OS-keyed):
        preferences.wallpaper_folders.<darwin|linux>.<theme> = path
    Falls back to a legacy flat schema:
        preferences.wallpaper_folders.<theme> = path
    """
    user_data = load_yaml(USER_DATA)
    folders = user_data.get("preferences", {}).get("wallpaper_folders", {})

    platform = "darwin" if sys.platform == "darwin" else "linux"
    os_folders = folders.get(platform)

    if isinstance(os_folders, dict):
        raw = os_folders.get(theme_name)
    else:
        raw = folders.get(theme_name)  # legacy flat schema

    if not raw:
        return None
    return Path(raw).expanduser()


def save_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)


VALID_TRANSITIONS = {
    "none", "simple", "fade", "left", "right", "top", "bottom",
    "wipe", "wave", "grow", "center", "any", "outer", "random",
}

DEFAULT_TRANSITION = "simple"
DEFAULT_POS = "center"
DEFAULT_ANGLE = "45"

# awww --transition-pos aliases (grow/outer circle center).
VALID_POSITIONS = {
    "center", "top", "left", "right", "bottom",
    "top-left", "top-right", "bottom-left", "bottom-right",
}

# Types that use --transition-pos (circle) vs --transition-angle (directional).
POS_TYPES = {"grow", "outer"}
ANGLE_TYPES = {"wipe", "wave"}
_COORD_RE = re.compile(r"^-?\d+(\.\d+)?,-?\d+(\.\d+)?$")


def validate_transition(value: str) -> str:
    if value not in VALID_TRANSITIONS:
        raise click.ClickException(
            f"Invalid transition '{value}'. Valid: {', '.join(sorted(VALID_TRANSITIONS))}"
        )
    return value


def validate_pos(value: str) -> str:
    if value in VALID_POSITIONS or _COORD_RE.match(value):
        return value
    raise click.ClickException(
        f"Invalid position '{value}'. Valid: {', '.join(sorted(VALID_POSITIONS))} or 'x,y'"
    )


def validate_angle(value: str) -> str:
    try:
        angle = float(value)
    except (TypeError, ValueError):
        raise click.ClickException(f"Invalid angle '{value}' (expected 0-360)")
    if not 0 <= angle <= 360:
        raise click.ClickException(f"Angle out of range '{value}' (expected 0-360)")
    return str(int(angle)) if angle.is_integer() else str(angle)


def get_transition() -> str:
    state = load_yaml(WALLPAPER_DATA)
    return state.get("wallpaper", {}).get("transition", DEFAULT_TRANSITION)


def get_transition_pos() -> str:
    state = load_yaml(WALLPAPER_DATA)
    return state.get("wallpaper", {}).get("transition_pos", DEFAULT_POS)


def get_transition_angle() -> str:
    state = load_yaml(WALLPAPER_DATA)
    return str(state.get("wallpaper", {}).get("transition_angle", DEFAULT_ANGLE))


def save_transition_fields(
    ttype: str | None = None, pos: str | None = None, angle: str | None = None
) -> None:
    """Persist transition fields without clobbering other wallpaper state."""
    state = load_yaml(WALLPAPER_DATA)
    wallpaper = state.setdefault("wallpaper", {})
    if ttype is not None:
        wallpaper["transition"] = ttype
    if pos is not None:
        wallpaper["transition_pos"] = pos
    if angle is not None:
        wallpaper["transition_angle"] = angle
    save_yaml(WALLPAPER_DATA, state)


def set_wallpaper_os(
    image_path: Path,
    transition: str | None = None,
    pos: str | None = None,
    angle: str | None = None,
):
    """Set wallpaper (OS-specific)"""
    if sys.platform == "darwin":
        script = f'''
        tell application "System Events"
            tell every desktop
                set picture to POSIX file "{image_path}"
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", script], check=True)
    elif sys.platform == "linux":
        if subprocess.run(["which", "awww"], capture_output=True).returncode != 0:
            raise click.ClickException("No wallpaper tool found. Install awww.")

        cmd = ["awww", "img", "--resize", "crop", str(image_path)]
        if transition:
            validate_transition(transition)
            cmd += ["--transition-type", transition]
            if transition not in ("simple", "none"):
                cmd += ["--transition-duration", "0.45", "--transition-fps", "90"]
            if transition in POS_TYPES and pos:
                cmd += ["--transition-pos", validate_pos(pos)]
            if transition in ANGLE_TYPES and angle:
                cmd += ["--transition-angle", validate_angle(angle)]
        subprocess.run(cmd, check=True)


@click.group()
def cli():
    """Universal Wallpaper Manager"""
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--transition", default=None, help="awww transition type")
@click.option("--pos", default=None, help="circle position for grow/outer")
@click.option("--angle", default=None, help="angle for wipe/wave")
def set(path: Path, transition: str | None, pos: str | None, angle: str | None):
    """Set wallpaper"""
    if path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
        raise click.ClickException(f"Unsupported format: {path.suffix}")

    console.print(f"[blue]🖼️  Setting wallpaper: {path.name}[/blue]")

    # Fall back to the persisted preference when not given, so the keybinding
    # (which passes nothing) honors the app's full transition choice.
    effective_transition = transition or get_transition()
    effective_pos = pos or get_transition_pos()
    effective_angle = angle or get_transition_angle()

    # Set wallpaper
    set_wallpaper_os(
        path,
        transition=effective_transition,
        pos=effective_pos,
        angle=effective_angle,
    )
    console.print("[green]✓ Wallpaper set[/green]")

    # Save state (merge so we don't clobber the transition preference)
    wallpaper_state = load_yaml(WALLPAPER_DATA)
    wallpaper_state.setdefault("wallpaper", {})
    wallpaper_state["wallpaper"]["current"] = str(path.absolute())
    wallpaper_state["wallpaper"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_yaml(WALLPAPER_DATA, wallpaper_state)

    # If dynamic theme, trigger re-extraction
    theme_data = load_yaml(THEME_DATA)
    if theme_data.get("theme", {}).get("name") == "dynamic":
        console.print("[blue]🎨 Dynamic theme - re-extracting colors...[/blue]")

        # Preserve current settings
        current_opacity = theme_data.get("theme", {}).get(
            "opacity", theme_data.get("theme", {}).get("transparency", 0)
        )
        current_contrast = theme_data.get("theme", {}).get("contrast", 0.0)

        # Build theme command - use uv run explicitly for subprocess compatibility
        # Note: mode is auto-detected from system appearance by theme-manager
        cmd = ["uv", "run", str(THEME_MANAGER), "set", "dynamic"]
        if current_opacity > 0:
            cmd.extend(["-o", str(current_opacity)])
        if current_contrast != 0.0:
            cmd.extend(["-c", str(current_contrast)])

        # Run theme manager and show output
        subprocess.run(cmd, check=True)
        console.print("[green]✓ Colors updated[/green]")
    elif sys.platform == "linux":
        # Static theme: palette is fixed, but hyprlock/wlogout bake blurred
        # backgrounds from the wallpaper image, so refresh just those. Linux
        # only (they are linux GUI apps; no-op on headless via the app filter).
        console.print("[blue]🖼️  Static theme - refreshing backgrounds...[/blue]")
        subprocess.run(
            ["uv", "run", str(THEME_MANAGER), "refresh-backgrounds"], check=True
        )
        console.print("[green]✓ Backgrounds updated[/green]")

    console.print("[green]✅ Done[/green]")


@cli.command(name="transition")
@click.argument("type_legacy", required=False)
@click.option("--type", "type_opt", default=None, help="transition type")
@click.option("--pos", default=None, help="circle position for grow/outer")
@click.option("--angle", default=None, help="angle for wipe/wave")
@click.option("--json", "as_json", is_flag=True, help="print full state as JSON")
def transition(
    type_legacy: str | None,
    type_opt: str | None,
    pos: str | None,
    angle: str | None,
    as_json: bool,
):
    """Get or set the shared transition preference (type + pos + angle).

    No set args  -> print current type (or full JSON with --json).
    Set args     -> persist so set/random (and Alt+Shift+W) honor them.
    """
    ttype = type_opt if type_opt is not None else type_legacy

    if ttype is None and pos is None and angle is None:
        if as_json:
            click.echo(
                json.dumps(
                    {
                        "type": get_transition(),
                        "pos": get_transition_pos(),
                        "angle": get_transition_angle(),
                    }
                )
            )
        else:
            click.echo(get_transition())
        return

    save_transition_fields(
        ttype=validate_transition(ttype) if ttype is not None else None,
        pos=validate_pos(pos) if pos is not None else None,
        angle=validate_angle(angle) if angle is not None else None,
    )
    click.echo(
        json.dumps(
            {
                "type": get_transition(),
                "pos": get_transition_pos(),
                "angle": get_transition_angle(),
            }
        )
    )


@cli.command(name="current-folder")
def current_folder():
    """Print the wallpaper folder for the current theme (OS-aware).

    Used by the Quickshell wallpaper panel to browse the right directory.
    Prints nothing if unresolved.
    """
    theme_data = load_yaml(THEME_DATA)
    theme_name = theme_data.get("theme", {}).get("name", "mocha")
    folder = resolve_wallpaper_folder(theme_name)
    if folder:
        click.echo(str(folder))


@cli.command()
def status():
    """Show current wallpaper"""
    state = load_yaml(WALLPAPER_DATA)
    current = state.get("wallpaper", {}).get("current")

    if current:
        console.print(f"\n[bold]🖼️  Wallpaper[/bold]\n  {current}\n")
    else:
        console.print("[yellow]No wallpaper set[/yellow]")


@cli.command()
@click.option("--transition", default=None, help="awww transition type")
@click.option("--pos", default=None, help="circle position for grow/outer")
@click.option("--angle", default=None, help="angle for wipe/wave")
def random(transition: str | None, pos: str | None, angle: str | None):
    """Set random wallpaper from theme folder"""
    console.print("[blue]🎲 Selecting random wallpaper...[/blue]")

    # Get current theme
    theme_data = load_yaml(THEME_DATA)
    theme_name = theme_data.get("theme", {}).get("name", "mocha")

    # Get wallpaper folder for theme (OS-aware)
    folder_path = resolve_wallpaper_folder(theme_name)

    if not folder_path:
        raise click.ClickException(
            f"No wallpaper folder configured for theme: {theme_name}"
        )

    if not folder_path.exists():
        raise click.ClickException(f"Wallpaper folder not found: {folder_path}")

    # Find all images
    image_extensions = [".jpg", ".jpeg", ".png", ".heic"]
    images = []
    for ext in image_extensions:
        images.extend(folder_path.glob(f"*{ext}"))
        images.extend(folder_path.glob(f"*{ext.upper()}"))

    if not images:
        raise click.ClickException(f"No images found in: {folder_path}")

    # Select random image
    selected = random_module.choice(images)
    console.print(f"[green]✓ Selected: {selected.name}[/green]")

    # Set wallpaper using the set command
    ctx = click.Context(set)
    ctx.invoke(set, path=selected, transition=transition, pos=pos, angle=angle)


if __name__ == "__main__":
    cli()
