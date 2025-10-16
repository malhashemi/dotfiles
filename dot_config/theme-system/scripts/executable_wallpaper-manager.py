#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["click>=8.0", "pyyaml>=6.0", "rich>=13.0"]
# ///

"""Universal Wallpaper Manager"""

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
        
        # Preserve current transparency setting
        current_transparency = theme_data.get('theme', {}).get('transparency', 0)
        cmd = [str(THEME_MANAGER), 'set', 'dynamic']
        if current_transparency > 0:
            cmd.extend(['-t', str(current_transparency)])
        
        subprocess.run(cmd)
    
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


if __name__ == '__main__':
    cli()
