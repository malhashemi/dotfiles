"""Flameshot theme generator"""

import configparser
from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, get_catppuccin_colors, is_dynamic_theme


class FlameshotTheme(BaseApp):
    """Flameshot screenshot tool theme generator

    Updates uiColor in flameshot.ini to match theme's primary color.
    Uses surgical INI editing to preserve user settings.

    Note: drawColor is the user's current tool color and resets when changed in UI.
          uiColor is the UI theme color and persists across sessions.

    Method: Inline surgical swap (configparser)
    """

    # GUI-only app - skip on headless systems
    requires_gui = True

    def __init__(self, config_home: Path):
        super().__init__("Flameshot", config_home)
        self.config_file = config_home / "flameshot/flameshot.ini"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to Flameshot by updating uiColor in INI"""

        # Check if config exists
        if not self.config_file.exists():
            self.log_warning(f"Config not found: {self.config_file}")
            self.log_warning("Skipping Flameshot theme update")
            return

        self.log_progress("Updating Flameshot UI color")

        # Get primary color from theme
        if is_dynamic_theme(theme_data):
            mat = get_material_colors(theme_data)
            primary_color = mat.get("primary", "#cba6f7")
        else:
            ctp = get_catppuccin_colors(theme_data)
            primary_color = ctp.get("mauve", "#cba6f7")

        # Surgically update uiColor in INI
        self._update_ui_color(primary_color)

        self.log_success(f"Flameshot uiColor set to {primary_color}")

    def _update_ui_color(self, color: str) -> None:
        """Update uiColor in flameshot.ini using configparser

        Args:
            color: Hex color string with # prefix (e.g., "#cba6f7")
        """
        config = configparser.RawConfigParser()

        # CRITICAL: Preserve case of keys (Flameshot is case-sensitive!)
        # Default behavior lowercases keys: uiColor -> uicolor (breaks Flameshot)
        config.optionxform = str  # type: ignore[assignment]

        config.read(self.config_file)

        # Ensure [General] section exists
        if "General" not in config:
            config["General"] = {}

        # Update only the uiColor value (preserve camelCase)
        config["General"]["uiColor"] = color

        # Write back to file
        with open(self.config_file, "w") as f:
            config.write(f)
