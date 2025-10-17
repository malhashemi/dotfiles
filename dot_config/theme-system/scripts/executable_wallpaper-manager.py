#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.0", "pyyaml>=6.0", "rich>=13.0"]
# ///

"""Universal Wallpaper Manager"""

import random as random_module
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
CHEZMOI_SOURCE = HOME / ".local/share/chezmoi"
THEME_DATA = CHEZMOI_SOURCE / ".chezmoidata/theme.yaml"
USER_DATA = CHEZMOI_SOURCE / ".chezmoidata/user.yaml"
WALLPAPER_DATA = CHEZMOI_SOURCE / ".chezmoidata/wallpaper-state.yaml"
THEME_MANAGER = CONFIG_HOME / "theme-system/scripts/theme-manager.py"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)


def set_wallpaper_os(image_path: Path):
    """Set wallpaper (OS-specific)"""
    if sys.platform == 'darwin':
        script = f'''
        tell application "System Events"
            tell every desktop
                set picture to POSIX file "{image_path}"
            end tell
        end tell
        '''
        subprocess.run(['osascript', '-e', script], check=True)
    elif sys.platform == 'linux':
        if subprocess.run(['which', 'swww'], capture_output=True).returncode == 0:
            subprocess.run(['swww', 'img', str(image_path)], check=True)
        else:
            raise click.ClickException("No wallpaper tool found. Install swww.")


@click.group()
def cli():
    """Universal Wallpaper Manager"""
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True, path_type=Path))
def set(path: Path):
    """Set wallpaper"""
    if path.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
        raise click.ClickException(f"Unsupported format: {path.suffix}")
    
    console.print(f"[blue]🖼️  Setting wallpaper: {path.name}[/blue]")
    
    # Set wallpaper
    set_wallpaper_os(path)
    console.print("[green]✓ Wallpaper set[/green]")
    
    # Save state
    wallpaper_state = {
        'wallpaper': {
            'current': str(path.absolute()),
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
    }
    save_yaml(WALLPAPER_DATA, wallpaper_state)
    
    # If dynamic theme, trigger re-extraction
    theme_data = load_yaml(THEME_DATA)
    if theme_data.get('theme', {}).get('name') == 'dynamic':
        console.print("[blue]🎨 Dynamic theme - re-extracting colors...[/blue]")
        
        # Preserve current settings
        current_opacity = theme_data.get('theme', {}).get('opacity',
            theme_data.get('theme', {}).get('transparency', 0))
        current_mode = theme_data.get('theme', {}).get('variant', 'dark')
        current_contrast = theme_data.get('theme', {}).get('contrast', 0.0)
        
        # Build theme command - use uv run explicitly for subprocess compatibility
        cmd = ['uv', 'run', str(THEME_MANAGER), 'set', 'dynamic']
        if current_opacity > 0:
            cmd.extend(['-o', str(current_opacity)])
        cmd.extend(['-m', current_mode])
        if current_contrast != 0.0:
            cmd.extend(['-c', str(current_contrast)])
        
        # Run theme manager and show output
        subprocess.run(cmd, check=True)
        console.print("[green]✓ Colors updated[/green]")
    
    console.print("[green]✅ Done[/green]")


@cli.command()
def status():
    """Show current wallpaper"""
    state = load_yaml(WALLPAPER_DATA)
    current = state.get('wallpaper', {}).get('current')
    
    if current:
        console.print(f"\n[bold]🖼️  Wallpaper[/bold]\n  {current}\n")
    else:
        console.print("[yellow]No wallpaper set[/yellow]")


@cli.command()
def random():
    """Set random wallpaper from theme folder"""
    console.print("[blue]🎲 Selecting random wallpaper...[/blue]")
    
    # Get current theme
    theme_data = load_yaml(THEME_DATA)
    theme_name = theme_data.get('theme', {}).get('name', 'mocha')
    
    # Get wallpaper folder for theme
    user_data = load_yaml(USER_DATA)
    wallpaper_folders = user_data.get('preferences', {}).get('wallpaper_folders', {})
    folder = wallpaper_folders.get(theme_name)
    
    if not folder:
        raise click.ClickException(f"No wallpaper folder configured for theme: {theme_name}")
    
    # Expand home directory
    folder_path = Path(folder).expanduser()
    
    if not folder_path.exists():
        raise click.ClickException(f"Wallpaper folder not found: {folder_path}")
    
    # Find all images
    image_extensions = ['.jpg', '.jpeg', '.png', '.heic']
    images = []
    for ext in image_extensions:
        images.extend(folder_path.glob(f'*{ext}'))
        images.extend(folder_path.glob(f'*{ext.upper()}'))
    
    if not images:
        raise click.ClickException(f"No images found in: {folder_path}")
    
    # Select random image
    selected = random_module.choice(images)
    console.print(f"[green]✓ Selected: {selected.name}[/green]")
    
    # Set wallpaper using the set command
    ctx = click.Context(set)
    ctx.invoke(set, path=selected)


if __name__ == '__main__':
    cli()
