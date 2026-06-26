"""wlogout logout-menu theme integration."""

import os
import subprocess
from pathlib import Path

import yaml

from .base import BaseApp
from utils import get_material_colors, get_opacity, build_css_palette


def _chezmoi_source() -> Path:
    """Resolve the chezmoi source dir (for the shared wallpaper state)."""
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


class WlogoutTheme(BaseApp):
    """Theme the wlogout power menu from the Material Design 3 palette.

    Writes:
      - colors.css     : @define-color palette (accents/borders, opacity-aware)
      - background.png  : the current wallpaper, heavily blurred, with the theme
                          opacity baked into its alpha channel so the desktop
                          shows through by (100 - opacity)%.

    The adopted wlogout glass theme `@import '../../colors.css'` and uses
    background.png as the window background.
    """

    requires_gui = True
    supported_platforms = ("linux",)
    wallpaper_derived = True

    def __init__(self, config_home: Path):
        super().__init__("wlogout", config_home)
        self.colors_file = config_home / "wlogout/colors.css"
        self.background_file = config_home / "wlogout/background.png"

    def apply_theme(self, theme_data: dict) -> None:
        mat = get_material_colors(theme_data)
        opacity = get_opacity(theme_data)

        self.log_progress("Updating wlogout colors")
        self.write_file(self.colors_file, build_css_palette(mat, opacity))
        self._render_background(theme_data, opacity)

    def _render_background(self, theme_data: dict, opacity: int) -> None:
        wallpaper = self._current_wallpaper(theme_data)
        if not wallpaper:
            self.log_warning("No current wallpaper; skipping wlogout background")
            return
        if not self.command_exists("magick"):
            self.log_warning("ImageMagick not found; skipping wlogout background")
            return

        self.background_file.parent.mkdir(parents=True, exist_ok=True)
        # Keep the blurred wallpaper prominent: map the theme opacity onto an
        # 80–100% alpha range (max 20-point drop), the same clamp used for walker
        # and the floating notifications, so the diffusion stays mostly solid and
        # low opacity reveals some of the live desktop behind.
        op = max(0, min(100, opacity))
        png_alpha = round(100 - (100 - op) * 0.20)
        # Heavy gaussian blur (diffusion look), then bake that alpha in.
        self.run_command(
            [
                "magick",
                str(wallpaper),
                "-resize", "1280x720^",
                "-gravity", "center",
                "-extent", "1280x720",
                "-blur", "0x28",
                "-alpha", "set",
                "-channel", "A",
                "-evaluate", "set", f"{png_alpha}%",
                "+channel",
                str(self.background_file),
            ],
            error_msg="wlogout background render failed",
            silent_fail=True,
            timeout=30,
        )

    def _current_wallpaper(self, theme_data: dict) -> str | None:
        # Dynamic themes carry the source wallpaper inline.
        wp = theme_data.get("theme", {}).get("source_wallpaper")
        if wp and Path(wp).exists():
            return wp

        # Otherwise read the shared wallpaper state (works for static themes too).
        state_file = _chezmoi_source() / ".chezmoidata/wallpaper-state.yaml"
        if not state_file.exists():
            return None
        try:
            data = yaml.safe_load(state_file.read_text()) or {}
        except yaml.YAMLError:
            return None
        wp = data.get("wallpaper", {}).get("current")
        return wp if wp and Path(wp).exists() else None
