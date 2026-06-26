"""GTK3 + GTK4 theming via generated, live-reloadable named themes.

Why named themes and not ~/.config/gtk-3.0/colors.css:
  Probed with a live GTK3 client on Wayland, GTK loads the *user* gtk.css (and
  its `@import colors.css`) once at startup and never re-reads it on a gtk-theme
  change. The *named theme's* CSS, however, IS re-read from disk whenever
  gtk-theme changes. So we generate a theme that imports the adw-gtk3 base
  (which honours the libadwaita @define-color names) and overrides those names
  from the MD3 palette, point gtk-theme at it, and reload by switching the name.

Why TWO alternating themes (-a / -b):
  Forcing the re-read needs a name *change*. Switching through the bare base
  theme flashes its default colours for a frame. Instead we keep two themes that
  BOTH carry the current palette and flip gtk-theme to whichever we're not on —
  the name changes (re-read happens) but every theme on the path already shows
  the final colours, so there is no flash.
"""

import subprocess
from pathlib import Path

from .base import BaseApp
from utils import (
    get_material_colors,
    get_theme_variant,
    build_gtk_palette,
    build_gtk3_palette,
)

_ICON_DARK = "Papirus-Dark"
_ICON_LIGHT = "Papirus-Light"
_CURSOR_THEME = "Bibata-Modern-Ice"
_CURSOR_SIZE = 24
_FONT_NAME = "Fira Sans Semi-Bold 11"

# Two alternating generated themes layered on the adw-gtk3 base (pkg:
# adw-gtk-theme), which honours the libadwaita @define-color names.
_THEME_A = "material-dynamic"
_THEME_B = "material-dynamic-b"
_THEMES = (_THEME_A, _THEME_B)
_BASE_DARK = "adw-gtk3-dark"
_BASE_LIGHT = "adw-gtk3"

# Widget fixups layered on the adw-gtk3 base. The base leaves selected icon/list
# labels white, unreadable on a bright (primary) accent selection in dark mode —
# force them to the accent's on-color so they always contrast.
_GTK3_FIXUPS = """
/* Readable selected text on the accent selection (esp. icon-view labels). */
.view:selected, .view:selected:focus,
iconview:selected, iconview:selected:focus,
treeview.view:selected, treeview.view:selected:focus,
list > row:selected, list > row:selected:focus,
flowboxchild:selected, flowboxchild:selected:focus {
    color: @theme_selected_fg_color;
}
"""


def _settings_ini(extended: bool, theme_name: str, prefer_dark: bool) -> str:
    lines = [
        "[Settings]",
        f"gtk-theme-name={theme_name}",
        f"gtk-application-prefer-dark-theme={1 if prefer_dark else 0}",
        f"gtk-icon-theme-name={_ICON_DARK if prefer_dark else _ICON_LIGHT}",
        f"gtk-font-name={_FONT_NAME}",
        f"gtk-cursor-theme-name={_CURSOR_THEME}",
        f"gtk-cursor-theme-size={_CURSOR_SIZE}",
    ]
    if extended:  # GTK3 understands the extra hints; GTK4 ignores them
        lines += [
            "gtk-toolbar-style=GTK_TOOLBAR_ICONS",
            "gtk-toolbar-icon-size=GTK_ICON_SIZE_LARGE_TOOLBAR",
            "gtk-button-images=0",
            "gtk-menu-images=0",
            "gtk-enable-event-sounds=1",
            "gtk-enable-input-feedback-sounds=0",
            "gtk-xft-antialias=1",
            "gtk-xft-hinting=1",
            "gtk-xft-hintstyle=hintslight",
            "gtk-xft-rgba=rgb",
        ]
    return "\n".join(lines) + "\n"


class GtkTheme(BaseApp):
    """Theme GTK3 + GTK4 apps from the Material Design 3 palette."""

    requires_gui = True
    supported_platforms = ("linux",)

    def __init__(self, config_home: Path):
        super().__init__("GTK", config_home)
        self.gtk_dirs = [config_home / "gtk-3.0", config_home / "gtk-4.0"]
        self.themes_root = config_home.parent / ".local" / "share" / "themes"

    def apply_theme(self, theme_data: dict) -> None:
        mat = get_material_colors(theme_data)
        libadwaita = build_gtk_palette(mat)
        gtk3 = libadwaita + build_gtk3_palette(mat)
        prefer_dark = get_theme_variant(theme_data) != "light"
        base = _BASE_DARK if prefer_dark else _BASE_LIGHT

        self.log_progress("Updating GTK theme")

        # Both alternating themes carry the new colours; switch to the one we're
        # NOT currently on so GTK3 re-reads, with no default-theme flash.
        self._write_themes(base, gtk3, libadwaita)
        target = self._next_theme()

        for gtk_dir in self.gtk_dirs:
            is_gtk3 = gtk_dir.name == "gtk-3.0"
            self.write_file(gtk_dir / "colors.css", gtk3 if is_gtk3 else libadwaita)
            self.write_file(
                gtk_dir / "settings.ini",
                _settings_ini(is_gtk3, target, prefer_dark),
            )

        self._reload(prefer_dark, target)

    def _write_themes(self, base: str, gtk3_colors: str, gtk4_colors: str) -> None:
        """Write both alternating themes, importing the adw-gtk3 base and
        overriding its @define-color names with the MD3 palette (overrides come
        after the import so the last @define-color wins)."""
        for name in _THEMES:
            tdir = self.themes_root / name
            self.write_file(
                tdir / "index.theme",
                "[Desktop Entry]\n"
                "Type=X-GNOME-Metatheme\n"
                f"Name={name}\n"
                "Comment=Generated by theme-system\n",
            )
            for sub, colors in (("gtk-3.0", gtk3_colors), ("gtk-4.0", gtk4_colors)):
                base_css = f'@import url("file:///usr/share/themes/{base}/{sub}/gtk.css");\n'
                extra = _GTK3_FIXUPS if sub == "gtk-3.0" else ""
                self.write_file(tdir / sub / "gtk.css", base_css + colors + extra)

    def _next_theme(self) -> str:
        """The alternate of the currently active theme (defaults to A)."""
        current = self._gget("org.gnome.desktop.interface", "gtk-theme")
        return _THEME_B if current == _THEME_A else _THEME_A

    def _reload(self, prefer_dark: bool, target: str) -> None:
        """Push the theme to running apps (Wayland reads these from gsettings,
        not settings.ini — sway wiki: GTK-3-settings-on-Wayland).

        - color-scheme: set (not pulsed) so GTK4/libadwaita follow light/dark
          without a light↔dark flash on palette-only changes.
        - gtk-theme: flip to the freshly-written alternate theme; the name change
          makes GTK3 re-read the theme CSS live, with no default-theme flash.
        """
        if not self.command_exists("gsettings"):
            return
        iface = "org.gnome.desktop.interface"
        self._gset(iface, "color-scheme", "prefer-dark" if prefer_dark else "prefer-light")
        self._gset(iface, "icon-theme", _ICON_DARK if prefer_dark else _ICON_LIGHT)
        self._gset(iface, "cursor-theme", _CURSOR_THEME)
        self._gset(iface, "gtk-theme", target)

    def _gget(self, schema: str, key: str) -> str:
        try:
            out = subprocess.run(
                ["gsettings", "get", schema, key],
                capture_output=True,
                text=True,
                timeout=3,
            ).stdout.strip()
            return out.strip("'")
        except (subprocess.SubprocessError, OSError):
            return ""

    def _gset(self, schema: str, key: str, value: str) -> None:
        self.run_command(
            ["gsettings", "set", schema, key, value], silent_fail=True, timeout=3
        )
