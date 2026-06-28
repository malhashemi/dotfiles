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
from .zed import ZedTheme
from .glow import GlowTheme
from .ghostty import GhosttyTheme
from .herdr import HerdrTheme
from .obsidian import ObsidianTheme
from .clipboard import ClipboardTheme
from .quickshell_bar import QuickshellBarTheme
from .quickshell_wallpaper import QuickshellWallpaperTheme
from .quickshell_voice import QuickshellVoiceTheme
from .hyprland import HyprlandTheme
from .gtk import GtkTheme
from .swaync import SwayncTheme
from .walker import WalkerTheme
from .wlogout import WlogoutTheme
from .hyprlock import HyprlockTheme
from .qt import QtTheme


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
        ZedTheme(config_home),
        GlowTheme(config_home),
        GhosttyTheme(config_home),
        HerdrTheme(config_home),
        ObsidianTheme(config_home),
        ClipboardTheme(config_home),
        QuickshellBarTheme(config_home),
        QuickshellWallpaperTheme(config_home),
        QuickshellVoiceTheme(config_home),
        HyprlandTheme(config_home),
        GtkTheme(config_home),
        SwayncTheme(config_home),
        WalkerTheme(config_home),
        WlogoutTheme(config_home),
        HyprlockTheme(config_home),
        QtTheme(config_home),
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
    "ZedTheme",
    "GlowTheme",
    "GhosttyTheme",
    "HerdrTheme",
    "ObsidianTheme",
    "ClipboardTheme",
    "QuickshellBarTheme",
    "QuickshellWallpaperTheme",
    "QuickshellVoiceTheme",
    "HyprlandTheme",
    "GtkTheme",
    "SwayncTheme",
    "WalkerTheme",
    "WlogoutTheme",
    "HyprlockTheme",
    "QtTheme",
    "get_all_apps",
]
