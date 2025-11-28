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
from .atuin import AtuinTheme
from .cava import CavaTheme
from .flameshot import FlameshotTheme
from .ncspot import NcspotTheme
from .nvim import NvimTheme
from .starship import StarshipTheme
from .btop import BtopTheme
from .television import TelevisionTheme
from .bottom import BottomTheme
from .opencode import OpencodeTheme
from .lazygit import LazygitTheme
from .posting import PostingTheme
from .yazi import YaziTheme
from .gitui import GituiTheme


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
        AtuinTheme(config_home),
        CavaTheme(config_home),
        FlameshotTheme(config_home),
        NcspotTheme(config_home),
        NvimTheme(config_home),
        StarshipTheme(config_home),
        BtopTheme(config_home),
        TelevisionTheme(config_home),
        BottomTheme(config_home),
        OpencodeTheme(config_home),
        LazygitTheme(config_home),
        PostingTheme(config_home),
        YaziTheme(config_home),
        GituiTheme(config_home),
    ]


__all__ = [
    "WeztermTheme",
    "BordersTheme",
    "SketchybarTheme",
    "AtuinTheme",
    "CavaTheme",
    "FlameshotTheme",
    "NcspotTheme",
    "NvimTheme",
    "StarshipTheme",
    "BtopTheme",
    "TelevisionTheme",
    "BottomTheme",
    "OpencodeTheme",
    "LazygitTheme",
    "PostingTheme",
    "YaziTheme",
    "GituiTheme",
    "get_all_apps",
]
