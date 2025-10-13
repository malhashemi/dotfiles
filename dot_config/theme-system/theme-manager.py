#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "click",
#     "pyyaml",
#     "jinja2",
# ]
# ///

"""
Theme System Manager v2
Unified theme management for all applications
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Dict, Optional, List
import click
import yaml

# Base paths
THEME_SYSTEM_DIR = Path.home() / ".config" / "theme-system"
STATE_DIR = THEME_SYSTEM_DIR / "state"
THEMES_DIR = THEME_SYSTEM_DIR / "themes"
SCRIPTS_DIR = THEME_SYSTEM_DIR / "scripts"
CACHE_DIR = THEME_SYSTEM_DIR / "cache"
CONFIG_FILE = THEME_SYSTEM_DIR / "config.yaml"

# Ensure directories exist
STATE_DIR.mkdir(parents=True, exist_ok=True)
THEMES_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

class ThemeManager:
    def __init__(self):
        self.config = self.load_config()
        self.current_theme = self.get_current_theme()
        
    def load_config(self) -> Dict:
        """Load configuration from config.yaml"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return yaml.safe_load(f)
        return {
            "default_theme": "mocha",
            "transparency": False,
            "apps": {}
        }
    
    def save_config(self):
        """Save configuration to config.yaml"""
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def get_current_theme(self) -> str:
        """Get the current active theme"""
        theme_file = STATE_DIR / "current-theme.txt"
        if theme_file.exists():
            return theme_file.read_text().strip()
        return self.config.get("default_theme", "mocha")
    
    def set_current_theme(self, theme: str):
        """Set the current active theme"""
        theme_file = STATE_DIR / "current-theme.txt"
        theme_file.write_text(theme)
        self.current_theme = theme
    
    def load_theme_definition(self, theme_name: str) -> Dict:
        """Load theme definition from JSON file"""
        theme_file = THEMES_DIR / f"catppuccin-{theme_name}.json"
        if theme_file.exists():
            with open(theme_file, 'r') as f:
                return json.load(f)
        return {}
    
    def apply_wezterm(self, theme: str, transparency: bool = False):
        """Apply theme to WezTerm"""
        theme_map = {
            "mocha": "Catppuccin Mocha Mauve",
            "frappe": "Catppuccin Frappe Mauve",
            "macchiato": "Catppuccin Macchiato Mauve",
            "latte": "Catppuccin Latte Mauve",
            "dynamic": "Dynamic"
        }
        
        # Write theme file
        theme_file = STATE_DIR / "wezterm-theme.txt"
        theme_file.write_text(theme_map.get(theme, "Catppuccin Mocha Mauve"))
        
        # Write transparency file
        transparent_file = STATE_DIR / "wezterm-transparent.txt"
        transparent_file.write_text("true" if transparency else "false")
        
        return True
    
    def apply_atuin(self, theme: str):
        """Apply theme to Atuin"""
        atuin_config = Path.home() / ".config" / "atuin" / "config.toml"
        
        if not atuin_config.exists():
            click.echo("⚠️  Atuin config not found")
            return False
        
        # Read config
        with open(atuin_config, 'r') as f:
            lines = f.readlines()
        
        # Theme mapping
        theme_name = f"catppuccin-{theme}-mauve" if theme != "dynamic" else None
        
        # Update config
        new_lines = []
        in_theme_section = False
        theme_section_found = False
        
        for line in lines:
            if line.strip() == "[theme]":
                in_theme_section = True
                theme_section_found = True
                if theme == "dynamic" or theme_name is None:
                    new_lines.append("# [theme]\n")
                else:
                    new_lines.append(line)
            elif in_theme_section and line.strip().startswith("name"):
                if theme == "dynamic" or theme_name is None:
                    new_lines.append(f'# name = "catppuccin-mocha-mauve"\n')
                else:
                    new_lines.append(f'name = "{theme_name}"\n')
                in_theme_section = False
            else:
                new_lines.append(line)
        
        # Add theme section if not found
        if not theme_section_found and theme != "dynamic":
            new_lines.append(f"\n[theme]\nname = \"{theme_name}\"\n")
        
        # Write back
        with open(atuin_config, 'w') as f:
            f.writelines(new_lines)
        
        return True
    
    def apply_opencode(self, theme: str):
        """Apply theme to OpenCode (requires restart)"""
        if theme == "dynamic":
            click.echo("  ℹ️  OpenCode doesn't support dynamic themes, using Mocha")
            theme = "mocha"
        
        opencode_config = Path.home() / ".config" / "opencode" / "opencode.json"
        
        config = {}
        if opencode_config.exists():
            with open(opencode_config, 'r') as f:
                config = json.load(f)
        
        config["theme"] = f"catppuccin-{theme}-mauve"
        
        opencode_config.parent.mkdir(exist_ok=True)
        with open(opencode_config, 'w') as f:
            json.dump(config, f, indent=2)
        
        return True
    
    def apply_all(self, theme: str, transparency: bool = False):
        """Apply theme to all configured applications"""
        results = {}
        
        # Apply to each app
        if self.config.get("apps", {}).get("wezterm", {}).get("enabled", True):
            results["wezterm"] = self.apply_wezterm(theme, transparency)
            
        if self.config.get("apps", {}).get("atuin", {}).get("enabled", True):
            results["atuin"] = self.apply_atuin(theme)
            
        if self.config.get("apps", {}).get("opencode", {}).get("enabled", True):
            results["opencode"] = self.apply_opencode(theme)
        
        # Save current theme
        self.set_current_theme(theme)
        self.config["current_theme"] = theme
        self.config["transparency"] = transparency
        self.save_config()
        
        return results

@click.group()
def cli():
    """Theme System Manager - Unified theme control"""
    pass

@cli.command()
@click.argument('theme', type=click.Choice(['mocha', 'frappe', 'macchiato', 'latte', 'dynamic']))
@click.option('--transparency', '-t', is_flag=True, help='Enable transparency')
@click.option('--app', multiple=True, help='Specific apps to theme')
def set(theme, transparency, app):
    """Set theme for applications"""
    manager = ThemeManager()
    
    click.echo(f"🎨 Setting theme: {theme}")
    
    if app:
        # Apply to specific apps
        for app_name in app:
            if app_name == "wezterm":
                if manager.apply_wezterm(theme, transparency):
                    click.echo(f"  ✅ WezTerm")
            elif app_name == "atuin":
                if manager.apply_atuin(theme):
                    click.echo(f"  ✅ Atuin")
            elif app_name == "opencode":
                if manager.apply_opencode(theme):
                    click.echo(f"  ✅ OpenCode (restart required)")
    else:
        # Apply to all apps
        results = manager.apply_all(theme, transparency)
        for app_name, success in results.items():
            if success:
                status = "✅"
                note = " (restart required)" if app_name == "opencode" else ""
            else:
                status = "❌"
                note = ""
            click.echo(f"  {status} {app_name.title()}{note}")
    
    if transparency:
        click.echo("  ✨ Transparency enabled")

@cli.command()
def toggle():
    """Toggle between mocha and latte themes"""
    manager = ThemeManager()
    current = manager.current_theme
    
    new_theme = "latte" if current != "latte" else "mocha"
    transparency = manager.config.get("transparency", False)
    
    click.echo(f"🔄 Toggling from {current} to {new_theme}")
    
    results = manager.apply_all(new_theme, transparency)
    for app_name, success in results.items():
        if success:
            click.echo(f"  ✅ {app_name.title()}")

@cli.command()
def status():
    """Show current theme status"""
    manager = ThemeManager()
    
    click.echo("🎨 Theme System Status")
    click.echo("─" * 40)
    click.echo(f"Current theme: {manager.current_theme}")
    click.echo(f"Transparency: {'✅' if manager.config.get('transparency') else '❌'}")
    click.echo()
    
    # Check individual app states
    click.echo("📱 Application States:")
    
    # WezTerm
    wezterm_theme_file = STATE_DIR / "wezterm-theme.txt"
    if wezterm_theme_file.exists():
        wezterm_theme = wezterm_theme_file.read_text().strip()
        click.echo(f"  WezTerm: {wezterm_theme}")
    
    # Atuin
    atuin_config = Path.home() / ".config" / "atuin" / "config.toml"
    if atuin_config.exists():
        with open(atuin_config, 'r') as f:
            for line in f:
                if line.strip().startswith("name") and "catppuccin" in line:
                    theme_name = line.split('"')[1]
                    click.echo(f"  Atuin: {theme_name}")
                    break
    
    # OpenCode
    opencode_config = Path.home() / ".config" / "opencode" / "opencode.json"
    if opencode_config.exists():
        with open(opencode_config, 'r') as f:
            config = json.load(f)
            if "theme" in config:
                click.echo(f"  OpenCode: {config['theme']}")

@cli.command()
@click.option('--on/--off', default=None, help='Enable or disable transparency')
def transparency(on):
    """Toggle or set transparency"""
    manager = ThemeManager()
    
    if on is None:
        # Toggle
        current = manager.config.get("transparency", False)
        new_state = not current
    else:
        new_state = on
    
    # Apply to WezTerm
    manager.apply_wezterm(manager.current_theme, new_state)
    manager.config["transparency"] = new_state
    manager.save_config()
    
    if new_state:
        click.echo("✨ Transparency enabled")
    else:
        click.echo("🪟 Transparency disabled")

@cli.command()
@click.option('--theme', is_flag=True, help='Also generate theme from wallpaper')
def wallpaper(theme):
    """Set random wallpaper and optionally generate dynamic theme"""
    script = SCRIPTS_DIR / "wallpaper-manager.sh"
    
    if not script.exists():
        click.echo("❌ Wallpaper manager script not found")
        return
    
    cmd = [str(script), "random"]
    if theme:
        cmd.append("--theme")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        click.echo(result.stdout)
    else:
        click.echo(f"❌ Error: {result.stderr}")

@cli.command()
def dynamic():
    """Generate and apply dynamic theme from current wallpaper"""
    manager = ThemeManager()
    
    click.echo("🎨 Generating dynamic theme from wallpaper...")
    
    # Run wallpaper theme generation
    script = SCRIPTS_DIR / "wallpaper-manager.sh"
    if script.exists():
        result = subprocess.run([str(script), "theme"], capture_output=True, text=True)
        if result.returncode == 0:
            click.echo("✅ Dynamic theme generated")
            
            # Apply dynamic theme
            results = manager.apply_all("dynamic", manager.config.get("transparency", False))
            for app_name, success in results.items():
                if success:
                    click.echo(f"  ✅ {app_name.title()}")
        else:
            click.echo(f"❌ Failed to generate theme: {result.stderr}")
    else:
        click.echo("❌ Wallpaper manager not found")

if __name__ == "__main__":
    cli()