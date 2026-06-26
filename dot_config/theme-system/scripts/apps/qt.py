"""Qt (qt6ct) theme integration via a generated QPalette color scheme.

qt5ct/qt6ct read a ColorScheme .conf describing 21 QPalette roles for each of
the active/disabled/inactive groups. We generate that file from the Material
Design 3 palette; the static, chezmoi-managed qt6ct.conf points
`color_scheme_path` at it with `custom_palette=true` + `style=Fusion` so the
palette is actually honored. Qt apps pick up the change on next launch
(QT_QPA_PLATFORMTHEME=qt6ct is exported from the Hyprland environment).
"""

from pathlib import Path

from .base import BaseApp
from utils import get_material_colors


def _argb(hex_color: str, alpha: str = "ff") -> str:
    """Convert ``#rrggbb`` to the qt6ct ``#aarrggbb`` form."""
    return f"#{alpha}{hex_color.lstrip('#')[-6:].lower()}"


class QtTheme(BaseApp):
    """Theme Qt (qt6ct) apps from the Material Design 3 palette."""

    requires_gui = True
    supported_platforms = ("linux",)

    def __init__(self, config_home: Path):
        super().__init__("Qt", config_home)
        self.scheme_file = config_home / "qt6ct" / "colors" / "dynamic.conf"

    def apply_theme(self, theme_data: dict) -> None:
        mat = get_material_colors(theme_data)
        self.log_progress("Updating Qt colors")
        self.write_file(self.scheme_file, self._build_scheme(mat))
        self.log_warning("Restart Qt apps to pick up the new palette")

    def _build_scheme(self, mat: dict) -> str:
        g = mat.get
        # QPalette roles in qt5ct/qt6ct ColorScheme order (21 roles).
        roles = [
            g("on_surface", "#cdd6f4"),                # 0  WindowText
            g("surface_container", "#313244"),         # 1  Button
            g("surface_container_high", "#45475a"),    # 2  Light
            g("surface_container", "#313244"),         # 3  Midlight
            g("surface_dim", "#11111b"),               # 4  Dark
            g("outline", "#6c7086"),                   # 5  Mid
            g("on_surface", "#cdd6f4"),                # 6  Text
            g("error", "#f38ba8"),                     # 7  BrightText
            g("on_surface", "#cdd6f4"),                # 8  ButtonText
            g("surface_container_lowest", "#11111b"),  # 9  Base
            g("surface", "#1e1e2e"),                   # 10 Window
            g("shadow", "#000000"),                    # 11 Shadow
            g("primary", "#89b4fa"),                   # 12 Highlight
            g("on_primary", "#1e1e2e"),                # 13 HighlightedText
            g("primary", "#89b4fa"),                   # 14 Link
            g("tertiary", "#a6e3a1"),                  # 15 LinkVisited
            g("surface_container_low", "#181825"),     # 16 AlternateBase
            g("surface", "#1e1e2e"),                   # 17 NoRole
            g("inverse_surface", "#cdd6f4"),           # 18 ToolTipBase
            g("inverse_on_surface", "#1e1e2e"),        # 19 ToolTipText
            g("on_surface_variant", "#a6adc8"),        # 20 PlaceholderText
        ]
        active = [_argb(c) for c in roles]
        active[20] = _argb(roles[20], "80")  # placeholder text is semi-transparent

        # Disabled group: mute the text-bearing roles toward the outline colour.
        disabled = list(active)
        muted = _argb(g("outline", "#6c7086"))
        for i in (0, 6, 8, 13):  # WindowText, Text, ButtonText, HighlightedText
            disabled[i] = muted

        inactive = list(active)

        def row(key: str, vals: list[str]) -> str:
            return f"{key}={', '.join(vals)}"

        return (
            "\n".join(
                [
                    "[ColorScheme]",
                    row("active_colors", active),
                    row("disabled_colors", disabled),
                    row("inactive_colors", inactive),
                ]
            )
            + "\n"
        )
