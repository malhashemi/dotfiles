"""Quickshell wallpaper-app theme integration.

Writes the full Material Design 3 palette consumed by the dedicated Quickshell
wallpaper instance (~/.config/quickshell/wallpaper) and asks it to reload.
"""

import json
import os
import subprocess
from pathlib import Path

import yaml

from .base import BaseApp
from utils import get_material_colors


def _chezmoi_source() -> Path:
    """Resolve the chezmoi source dir (for user.yaml wallpaper folders)."""
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

    xdg_data = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))
    return Path(xdg_data) / "chezmoi"


def _resolve_wallpaper_folder(theme_name: str) -> str:
    """Resolve the wallpaper browse folder for the current theme.

    Source of truth is .chezmoidata/user.yaml preferences.wallpaper_folders,
    the same mapping wallpaper-manager.py uses for `random`.
    """
    default = str(Path.home() / "Pictures/Wallpapers")
    user_data_path = _chezmoi_source() / ".chezmoidata/user.yaml"
    if not user_data_path.exists():
        return default

    try:
        data = yaml.safe_load(user_data_path.read_text()) or {}
    except yaml.YAMLError:
        return default

    folders = data.get("preferences", {}).get("wallpaper_folders", {})
    folder = folders.get(theme_name) or folders.get("dynamic") or default
    folder = folder.replace("$HOME", str(Path.home()))
    return str(Path(folder).expanduser())


# Keys consumed by the wallpaper instance's Theme singleton.
THEME_KEYS = [
    "background",
    "error",
    "error_container",
    "inverse_on_surface",
    "inverse_primary",
    "inverse_surface",
    "on_background",
    "on_error",
    "on_error_container",
    "on_primary",
    "on_primary_container",
    "on_primary_fixed",
    "on_primary_fixed_variant",
    "on_secondary",
    "on_secondary_container",
    "on_secondary_fixed",
    "on_secondary_fixed_variant",
    "on_surface",
    "on_surface_variant",
    "on_tertiary",
    "on_tertiary_container",
    "on_tertiary_fixed",
    "on_tertiary_fixed_variant",
    "outline",
    "outline_variant",
    "primary",
    "primary_container",
    "primary_fixed",
    "primary_fixed_dim",
    "scrim",
    "secondary",
    "secondary_container",
    "secondary_fixed",
    "secondary_fixed_dim",
    "shadow",
    "source_color",
    "surface",
    "surface_bright",
    "surface_container",
    "surface_container_high",
    "surface_container_highest",
    "surface_container_low",
    "surface_container_lowest",
    "surface_dim",
    "surface_tint",
    "surface_variant",
    "tertiary",
    "tertiary_container",
    "tertiary_fixed",
    "tertiary_fixed_dim",
]


class QuickshellWallpaperTheme(BaseApp):
    """Full MD3 color contract for the Quickshell wallpaper instance."""

    requires_gui = True
    supported_platforms = ("linux",)

    def __init__(self, config_home: Path):
        super().__init__("Quickshell Wallpaper", config_home)
        self.instance_dir = config_home / "quickshell/wallpaper"
        self.colors_file = self.instance_dir / "colors.json"

    def apply_theme(self, theme_data: dict) -> None:
        mat = get_material_colors(theme_data)
        colors = {key: mat[key] for key in THEME_KEYS if key in mat}

        self.log_progress("Updating Quickshell wallpaper colors")
        self.write_file(self.colors_file, json.dumps(colors, indent=2) + "\n")
        self._reload_instance()

    def _reload_instance(self) -> None:
        if not self.command_exists("qs"):
            return

        # Silent: the instance may not be running.
        self.run_command(
            [
                "qs",
                "-p",
                str(self.instance_dir),
                "ipc",
                "call",
                "theme-manager",
                "reload",
            ],
            error_msg="Quickshell wallpaper instance not running",
            silent_fail=True,
        )
