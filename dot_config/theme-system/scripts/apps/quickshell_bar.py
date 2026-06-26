"""Quickshell bar theme integration."""

import json
from pathlib import Path

from .base import BaseApp
from utils import get_material_colors


class QuickshellBarTheme(BaseApp):
    """Generate the local color contract consumed by the custom Quickshell bar."""

    requires_gui = True
    supported_platforms = ("linux",)

    # Core tokens the bar has always used, plus the extra Material Design 3
    # roles the theme-control popup needs (chips, sliders, accents-on-accent).
    THEME_KEYS = [
        "background",
        "primary",
        "on_surface",
        "outline",
        "on_primary",
        "secondary",
        "tertiary",
        "error",
        "surface_container",
        "surface_container_high",
        "primary_container",
    ]

    # Guaranteed-present fallbacks so the bar never reads an empty contract.
    DEFAULTS = {
        "background": "#1e1e2e",
        "primary": "#cba6f7",
        "on_surface": "#cdd6f4",
        "outline": "#6c7086",
    }

    def __init__(self, config_home: Path):
        super().__init__("Quickshell Bar", config_home)
        self.instance_dir = config_home / "quickshell/bar"
        self.colors_file = self.instance_dir / "colors.json"

    def apply_theme(self, theme_data: dict) -> None:
        """Write ~/.config/quickshell/bar/colors.json from MD3 theme colors."""
        mat = get_material_colors(theme_data)

        colors = dict(self.DEFAULTS)
        for key in self.THEME_KEYS:
            if key in mat:
                colors[key] = mat[key]

        self.log_progress("Updating Quickshell bar colors")
        self.write_file(self.colors_file, json.dumps(colors, indent=2) + "\n")
        self._reload_instance()

    def _reload_instance(self) -> None:
        """Ask the running bar to re-read its colors (no-op if not running)."""
        if not self.command_exists("qs"):
            return

        self.run_command(
            [
                "qs",
                "-p",
                str(self.instance_dir),
                "ipc",
                "call",
                "bar",
                "reload",
            ],
            error_msg="Quickshell bar instance not running",
            silent_fail=True,
        )
