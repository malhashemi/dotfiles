"""Walker launcher theme integration."""

from pathlib import Path

from .base import BaseApp
from utils import get_material_colors, get_opacity, build_css_palette


class WalkerTheme(BaseApp):
    """Generate the @define-color palette consumed by the Walker theme.

    The adopted Walker `catppuccin` theme `@import '../../colors.css'` and styles
    itself entirely from the Material Design 3 named colors. Walker is launched
    fresh on every keybind, so the next invocation picks up the regenerated
    colors.css — there is no persistent process to reload.
    """

    requires_gui = True
    supported_platforms = ("linux",)

    def __init__(self, config_home: Path):
        super().__init__("Walker", config_home)
        self.colors_file = config_home / "walker/colors.css"

    def apply_theme(self, theme_data: dict) -> None:
        mat = get_material_colors(theme_data)
        opacity = get_opacity(theme_data)

        self.log_progress("Updating Walker colors")
        self.write_file(self.colors_file, build_css_palette(mat, opacity))
