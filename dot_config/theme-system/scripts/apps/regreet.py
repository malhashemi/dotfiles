"""regreet (greetd login greeter) — wallpaper-following theme integration.

regreet runs as the unprivileged ``greeter`` user out of ``/etc/greetd`` and
cannot read ``$HOME``, so this plugin renders the greeter's theme into a shared,
greeter-readable directory that the desktop user owns:

    /var/lib/regreet-theme/bg.png       blurred current wallpaper  (regreet [background])
    /var/lib/regreet-theme/regreet.css  libadwaita @define-color palette + structural CSS
                                        (loaded via ``regreet --style``)

The directory is created **user-owned** once by the privileged greetd setup
script (``install -d -o <user> -m 0755 /var/lib/regreet-theme``). This plugin
only writes into it — it never needs sudo — and skips gracefully when the
directory is absent (machines without the greetd login stack, or before setup
has run). regreet re-reads both files at every login, so the greeter follows the
wallpaper / matugen palette exactly like the hyprlock lock screen.
"""

import os
import subprocess
from pathlib import Path

import yaml

from .base import BaseApp
from utils import get_material_colors
from utils.colors import build_gtk_palette, build_css_palette


# Shared, greeter-readable output dir. Created user-owned by the greetd setup
# script; this plugin only writes into it (never sudo).
GREETER_DIR = Path("/var/lib/regreet-theme")


# Artistic structural CSS, layered on the FULL MD3 palette emitted above
# (build_css_palette = every role; build_gtk_palette = libadwaita aliases).
# Targets regreet's real widget tree from upstream src/gui/templates.rs
# (gtk::Overlay > gtk::Picture background + gtk::Frame.background "cards"). Two
# deliberate choices, both learned from previewing:
#   * the wallpaper is painted via CSS `background-image` on `window`, because
#     regreet's GstPlay background path does not render a still PNG here;
#   * the Login button's LABEL is coloured explicitly (@on_primary) — Adwaita's
#     .suggested-action otherwise forces an unreadable white label on the accent.
_STRUCTURAL_CSS = """
/* ===== regreet greeter — theme-system artistic styling ====================== */

* { font-family: "JetBrainsMono Nerd Font", monospace; }

/* Wallpaper, painted via CSS (reliable for a still PNG) with a soft primary→
   tertiary tint for depth. The Picture widget stays empty/transparent on top. */
window {
    color: @on_surface;
    background-color: @surface;
    background-image:
        linear-gradient(135deg,
            alpha(@primary_container, 0.42),
            alpha(@surface, 0.28) 45%,
            alpha(@tertiary_container, 0.42)),
        url("file:///var/lib/regreet-theme/bg.png");
    background-size: cover, cover;
    background-position: center, center;
    background-repeat: no-repeat, no-repeat;
}

/* Labels get a soft text-shadow so they stay legible over the see-through cards. */
label { color: @on_surface; text-shadow: 0 1px 3px alpha(@scrim, 0.65); }

/* Login + clock: frosted GLASS. The surface tint is kept genuinely low-opacity so
   the blurred wallpaper clearly shows THROUGH the card (that is the "glass"), with
   a faint light rim as the glass edge. Tune the one alpha below: higher = more
   solid/opaque, lower = more glassy/see-through. */
frame.background {
    background-color: alpha(@surface_container, 0.45);
    border: 1px solid alpha(@on_surface, 0.18);
    border-radius: 22px;
    padding: 22px;
}

/* Inputs + dropdowns. */
entry, entry > text, combobox, combobox button {
    background-color: alpha(@surface_container_highest, 0.55);
    color: @on_surface;
    border: 1px solid @outline_variant;
    border-radius: 12px;
    min-height: 40px;
}
entry:focus-within, combobox button:focus-within {
    border-color: @primary;
    box-shadow: 0 0 0 2px alpha(@primary, 0.35);
}

/* ── Buttons: shape + fill go on the BUTTON, colour on the LABEL only — so the
   label never draws its own inner border box, and Adwaita's forced label
   colours are overridden. Hover is always a shade of primary. ── */
button {
    background-image: none;
    background-color: alpha(@secondary_container, 0.90);
    border: 1px solid alpha(@outline, 0.45);
    border-radius: 12px;
    min-height: 40px;
    padding: 6px 16px;
}
button label { color: @on_secondary_container; }
button image { color: @on_secondary_container; }   /* the edit-pencil icons */

button:hover {
    background-color: alpha(@primary_container, 0.95);
    border-color: @primary;
}
button:hover label, button:hover image { color: @on_primary_container; }

/* Login (suggested-action): primary fill, dark readable label. */
button.suggested-action { background-color: @primary; border-color: @primary; }
button.suggested-action label { color: @on_primary; font-weight: bold; }
button.suggested-action:hover { background-color: @primary_fixed; }
button.suggested-action:hover label { color: @on_primary; }

/* Reboot / Power Off (destructive-action): subtle error base, primary hover,
   and NO border on the label (that was the rectangle around the text). */
button.destructive-action { background-color: alpha(@error, 0.16); border-color: alpha(@error, 0.45); }
button.destructive-action label { color: @on_surface; }
button.destructive-action:hover { background-color: alpha(@primary_container, 0.95); border-color: @primary; }
button.destructive-action:hover label { color: @on_primary_container; }
"""


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


class RegreetTheme(BaseApp):
    """Theme the greetd ``regreet`` login greeter from the wallpaper + MD3 palette.

    Writes (both into the greeter-readable ``/var/lib/regreet-theme``):
      - regreet.css : libadwaita ``@define-color`` overrides + structural CSS,
                      loaded by ``regreet --style``
      - bg.png      : the current wallpaper, heavily blurred and fully opaque
                      (same render as hyprlock), painted via CSS ``background-image``
    """

    requires_gui = True
    supported_platforms = ("linux",)
    wallpaper_derived = True

    def __init__(self, config_home: Path):
        super().__init__("regreet", config_home)
        self.css_file = GREETER_DIR / "regreet.css"
        self.background_file = GREETER_DIR / "bg.png"

    def apply_theme(self, theme_data: dict) -> None:
        # The greeter-readable dir is created (user-owned) by the privileged
        # greetd setup script. If it's absent or unwritable, the greetd login
        # stack isn't set up on this machine — skip silently (no sudo, no error).
        if not (GREETER_DIR.is_dir() and os.access(GREETER_DIR, os.W_OK)):
            return

        mat = get_material_colors(theme_data)
        opacity = int(theme_data.get("theme", {}).get("opacity", 100))

        self.log_progress("Updating regreet greeter theme")
        # Full MD3 palette (build_css_palette emits every role) + libadwaita
        # aliases (build_gtk_palette) so the CSS below can use the whole palette.
        css = build_css_palette(mat, opacity) + build_gtk_palette(mat) + _STRUCTURAL_CSS
        self.write_file(self.css_file, css)

        self._render_background(theme_data)

    def _render_background(self, theme_data: dict) -> None:
        wallpaper = self._current_wallpaper(theme_data)
        if not wallpaper:
            self.log_warning("No current wallpaper; skipping regreet background")
            return
        if not self.command_exists("magick"):
            self.log_warning("ImageMagick not found; skipping regreet background")
            return

        # Heavy gaussian blur (diffusion), fully opaque — a frosted login backdrop
        # matching the hyprlock lock screen.
        self.run_command(
            [
                "magick",
                str(wallpaper),
                "-resize", "2560x1440^",
                "-gravity", "center",
                "-extent", "2560x1440",
                "-blur", "0x32",
                str(self.background_file),
            ],
            error_msg="regreet background render failed",
            silent_fail=True,
            timeout=30,
        )

    def _current_wallpaper(self, theme_data: dict) -> str | None:
        wp = theme_data.get("theme", {}).get("source_wallpaper")
        if wp and Path(wp).exists():
            return wp

        state_file = _chezmoi_source() / ".chezmoidata/wallpaper-state.yaml"
        if not state_file.exists():
            return None
        try:
            data = yaml.safe_load(state_file.read_text()) or {}
        except yaml.YAMLError:
            return None
        wp = data.get("wallpaper", {}).get("current")
        return wp if wp and Path(wp).exists() else None
