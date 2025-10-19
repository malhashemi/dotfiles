"""Theme-aware application modules

This module provides a registry of all applications that support theming.
To add a new app:
1. Create apps/newapp.py with NewAppTheme(BaseApp)
2. Import it here
3. Add to get_all_apps() list
"""

from pathlib import Path
from .wezterm import WeztermTheme
from .borders import BordersTheme
from .sketchybar import SketchybarTheme


def get_all_apps(config_home: Path) -> list:
    """Get all registered theme-aware applications
    
    Args:
        config_home: Path to ~/.config directory
        
    Returns:
        List of app instances ready to receive theme updates
        
    Example:
        >>> apps = get_all_apps(Path.home() / ".config")
        >>> for app in apps:
        ...     app.apply_theme(theme_data)
    """
    return [
        WeztermTheme(config_home),
        BordersTheme(config_home),
        SketchybarTheme(config_home),
    ]


__all__ = [
    "WeztermTheme",
    "BordersTheme",
    "SketchybarTheme",
    "get_all_apps",
]
