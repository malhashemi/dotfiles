"""Clipboard CLI theme generator"""

from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, get_catppuccin_colors, is_dynamic_theme


class ClipboardTheme(BaseApp):
    """Clipboard CLI theme generator

    Method: external_file (generates plain text theme file)
    Reload: Instant - env var read on each cb command execution

    Clipboard CLI uses CLIPBOARD_THEME environment variable for theming.
    No config file exists - all configuration via env vars.

    We generate a plain text file containing the theme value, which is then
    read by the shell config to set the CLIPBOARD_THEME env var.
    This approach is cross-platform (works with zsh, bash, PowerShell, fish, etc.)
    """

    def __init__(self, config_home: Path):
        super().__init__("clipboard", config_home)
        self.theme_file = config_home / "clipboard/theme"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to Clipboard CLI"""
        self.log_progress("Updating Clipboard theme")

        if is_dynamic_theme(theme_data):
            theme_value = self._generate_dynamic_theme(theme_data)
        else:
            theme_value = self._generate_static_theme(theme_data)

        # Write plain text file (just the theme value, no shell syntax)
        self.theme_file.parent.mkdir(parents=True, exist_ok=True)
        self.write_file(self.theme_file, theme_value)
        self.log_success(f"Clipboard theme: {self.theme_file}")

    def _generate_dynamic_theme(self, theme_data: dict) -> str:
        """Generate theme from Material Design 3 colors"""
        mat = get_material_colors(theme_data)

        # Map MD3 colors to clipboard categories
        help_rgb = self._hex_to_rgb(mat.get("primary", "#cba6f7"))
        info_rgb = self._hex_to_rgb(mat.get("secondary", "#89b4fa"))
        error_rgb = self._hex_to_rgb(mat.get("error", "#f38ba8"))
        success_rgb = self._hex_to_rgb(mat.get("tertiary", "#a6e3a1"))
        progress_rgb = self._hex_to_rgb(mat.get("primary_container", "#f5c2e7"))

        return f"help={help_rgb},info={info_rgb},error={error_rgb},success={success_rgb},progress={progress_rgb}"

    def _generate_static_theme(self, theme_data: dict) -> str:
        """Generate theme from Catppuccin colors"""
        colors = get_catppuccin_colors(theme_data)

        # Map Catppuccin colors to clipboard categories
        # help = mauve (user's favorite accent)
        # info = blue
        # error = red
        # success = green
        # progress = pink
        help_rgb = self._hex_to_rgb(colors.get("mauve", "#cba6f7"))
        info_rgb = self._hex_to_rgb(colors.get("blue", "#89b4fa"))
        error_rgb = self._hex_to_rgb(colors.get("red", "#f38ba8"))
        success_rgb = self._hex_to_rgb(colors.get("green", "#a6e3a1"))
        progress_rgb = self._hex_to_rgb(colors.get("pink", "#f5c2e7"))

        return f"help={help_rgb},info={info_rgb},error={error_rgb},success={success_rgb},progress={progress_rgb}"

    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convert hex color (#RRGGBB) to RGB format (r;g;b)"""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r};{g};{b}"
