"""Quickshell voice-typer HUD theme integration.

Writes the Material Design 3 palette consumed by the voice HUD Quickshell
instance (~/.config/quickshell/voice) and asks it to reload.
"""

import json
from pathlib import Path

from .base import BaseApp
from utils import get_material_colors

# Keys consumed by the voice HUD's Theme singleton.
THEME_KEYS = [
    "background",
    "error",
    "on_error",
    "on_surface",
    "on_surface_variant",
    "outline",
    "outline_variant",
    "primary",
    "on_primary",
    "primary_container",
    "secondary",
    "surface",
    "surface_container",
    "surface_container_high",
    "surface_container_highest",
    "tertiary",
]


class QuickshellVoiceTheme(BaseApp):
    """MD3 color contract for the Quickshell voice-typer HUD instance."""

    requires_gui = True
    supported_platforms = ("linux",)

    def __init__(self, config_home: Path):
        super().__init__("Quickshell Voice", config_home)
        self.instance_dir = config_home / "quickshell/voice"
        self.colors_file = self.instance_dir / "colors.json"

    def apply_theme(self, theme_data: dict) -> None:
        mat = get_material_colors(theme_data)
        colors = {key: mat[key] for key in THEME_KEYS if key in mat}

        self.log_progress("Updating Quickshell voice HUD colors")
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
                "voice",
                "reloadTheme",
            ],
            error_msg="Quickshell voice HUD instance not running",
            silent_fail=True,
        )
