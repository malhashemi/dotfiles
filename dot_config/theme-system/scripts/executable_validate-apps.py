#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0", "rich>=13.0"]
# ///

"""Validate apps.yaml schema for theme system"""

from pathlib import Path
import sys
import yaml
from rich.console import Console
from rich.table import Table

console = Console()

HOME = Path.home()
CHEZMOI_SOURCE = HOME / ".local/share/chezmoi"
APPS_YAML = CHEZMOI_SOURCE / ".chezmoidata/apps.yaml"

# Valid values for enum fields
VALID_METHODS = ["builtin", "external_file", "inline", "terminal_colors"]
VALID_FORMATS = ["lua", "lua_module", "toml", "yaml", "json", "conf", "kitty_conf"]
VALID_RELOAD_METHODS = ["file_watch", "signal", "manual", "instant"]
VALID_OPACITY_METHODS = ["external_file", "inline", "compositor"]
VALID_GENERATOR_METHODS = ["external_file", "surgical_swap", "full_template"]

def validate_app_schema(app_name: str, app_config: dict) -> list[str]:
    """Validate a single app's configuration"""
    errors = []
    
    # Required top-level fields
    required_fields = ["display_name", "config_file", "config_format", 
                      "static_theme", "dynamic_theme", "opacity", "reload", "generator"]
    
    for field in required_fields:
        if field not in app_config:
            errors.append(f"Missing required field: {field}")
    
    # Validate config_format
    if "config_format" in app_config:
        if app_config["config_format"] not in VALID_FORMATS:
            errors.append(f"Invalid config_format: {app_config['config_format']}")
    
    # Validate static_theme
    if "static_theme" in app_config:
        if "priority" not in app_config["static_theme"]:
            errors.append("static_theme missing 'priority' field")
        else:
            for idx, method_config in enumerate(app_config["static_theme"]["priority"]):
                if "method" not in method_config:
                    errors.append(f"static_theme.priority[{idx}] missing 'method'")
                elif method_config["method"] not in VALID_METHODS:
                    errors.append(f"static_theme.priority[{idx}] invalid method: {method_config['method']}")
                
                if "enabled" not in method_config:
                    errors.append(f"static_theme.priority[{idx}] missing 'enabled'")
    
    # Validate dynamic_theme
    if "dynamic_theme" in app_config:
        if "priority" not in app_config["dynamic_theme"]:
            errors.append("dynamic_theme missing 'priority' field")
        else:
            for idx, method_config in enumerate(app_config["dynamic_theme"]["priority"]):
                if "method" not in method_config:
                    errors.append(f"dynamic_theme.priority[{idx}] missing 'method'")
                elif method_config["method"] not in VALID_METHODS:
                    errors.append(f"dynamic_theme.priority[{idx}] invalid method: {method_config['method']}")
                
                if "enabled" not in method_config:
                    errors.append(f"dynamic_theme.priority[{idx}] missing 'enabled'")
    
    # Validate external_files (if present)
    if "external_files" in app_config:
        for file_type in ["colors", "opacity"]:
            if file_type in app_config["external_files"]:
                file_config = app_config["external_files"][file_type]
                required = ["path", "format", "template", "load_mechanism"]
                for field in required:
                    if field not in file_config:
                        errors.append(f"external_files.{file_type} missing '{field}'")
    
    # Validate opacity
    if "opacity" in app_config:
        if "supported" not in app_config["opacity"]:
            errors.append("opacity missing 'supported' field")
        
        if app_config["opacity"].get("supported"):
            if "method" not in app_config["opacity"]:
                errors.append("opacity missing 'method' field")
            elif app_config["opacity"]["method"] not in VALID_OPACITY_METHODS:
                errors.append(f"opacity invalid method: {app_config['opacity']['method']}")
    
    # Validate reload
    if "reload" in app_config:
        if "automatic" not in app_config["reload"]:
            errors.append("reload missing 'automatic' field")
        if "method" not in app_config["reload"]:
            errors.append("reload missing 'method' field")
        elif app_config["reload"]["method"] not in VALID_RELOAD_METHODS:
            errors.append(f"reload invalid method: {app_config['reload']['method']}")
    
    # Validate generator
    if "generator" in app_config:
        if "colors_function" not in app_config["generator"]:
            errors.append("generator missing 'colors_function' field")
        
        # Check if method is specified (optional but recommended)
        if "method" in app_config["generator"]:
            if app_config["generator"]["method"] not in VALID_GENERATOR_METHODS:
                errors.append(f"generator invalid method: {app_config['generator']['method']}")
    
    return errors


def validate_apps_yaml():
    """Validate the entire apps.yaml file"""
    console.print(f"[blue]📋 Validating {APPS_YAML}...[/blue]\n")
    
    if not APPS_YAML.exists():
        console.print(f"[red]❌ File not found: {APPS_YAML}[/red]")
        return False
    
    try:
        with open(APPS_YAML) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        console.print(f"[red]❌ YAML parsing error:[/red]")
        console.print(str(e))
        return False
    
    if not data:
        console.print("[red]❌ Empty or invalid YAML file[/red]")
        return False
    
    if "apps" not in data:
        console.print("[red]❌ Missing root 'apps' key[/red]")
        return False
    
    all_errors = {}
    for app_name, app_config in data["apps"].items():
        errors = validate_app_schema(app_name, app_config)
        if errors:
            all_errors[app_name] = errors
    
    if all_errors:
        console.print("[red]❌ Validation failed with errors:\n[/red]")
        
        for app_name, errors in all_errors.items():
            console.print(f"[yellow]{app_name}:[/yellow]")
            for error in errors:
                console.print(f"  - {error}")
            console.print()
        
        return False
    else:
        # Show summary table
        table = Table(title="✅ Apps Catalog Valid", show_header=True)
        table.add_column("App", style="cyan")
        table.add_column("Display Name", style="green")
        table.add_column("Config Format", style="yellow")
        table.add_column("Opacity", style="magenta")
        
        for app_name, app_config in data["apps"].items():
            opacity_status = "✅" if app_config.get("opacity", {}).get("supported") else "❌"
            table.add_row(
                app_name,
                app_config.get("display_name", ""),
                app_config.get("config_format", ""),
                opacity_status
            )
        
        console.print(table)
        console.print(f"\n[green]✅ All {len(data['apps'])} apps validated successfully![/green]")
        return True


if __name__ == "__main__":
    success = validate_apps_yaml()
    sys.exit(0 if success else 1)
