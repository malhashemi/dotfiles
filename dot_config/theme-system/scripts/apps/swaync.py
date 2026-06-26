"""SwayNC notification daemon theme integration."""

from pathlib import Path

from .base import BaseApp
from utils import get_material_colors, get_opacity, build_css_palette


class SwayncTheme(BaseApp):
    """Generate the @define-color palette consumed by the swaync stylesheet.

    The adopted swaync config's glass theme `@import '../../colors.css'` and
    styles itself entirely from those Material Design 3 named colors, so we just
    (re)write ~/.config/swaync/colors.css and hot-reload the CSS.
    """

    requires_gui = True
    supported_platforms = ("linux",)

    def __init__(self, config_home: Path):
        super().__init__("SwayNC", config_home)
        self.colors_file = config_home / "swaync/colors.css"

    def apply_theme(self, theme_data: dict) -> None:
        mat = get_material_colors(theme_data)
        opacity = get_opacity(theme_data)

        self.log_progress("Updating SwayNC colors")
        self.write_file(self.colors_file, build_css_palette(mat, opacity))

        if self.command_exists("swaync-client"):
            self.run_command(
                ["swaync-client", "--reload-css"],
                error_msg="SwayNC not running",
                silent_fail=True,
            )
