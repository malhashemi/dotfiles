"""Herdr terminal multiplexer theme integration"""

from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, get_theme_variant


class HerdrTheme(BaseApp):
    """Herdr terminal-multiplexer theme integration.

    Herdr is the TUI multiplexer that hosts agent panes. Its config lives at
    ~/.config/herdr/config.toml. By default it uses theme = "terminal" (inherits
    the host terminal's ANSI palette); this handler instead drives a dynamic
    [theme.custom] block from the Material Design 3 palette so Herdr's chrome
    (sidebar, panels, borders, accents) matches the wallpaper-driven theme used
    by Ghostty et al., rather than passively inheriting ANSI colors.

    Method: in-place rewrite of the [theme] + [theme.custom] sections only.
    Reload: `herdr server reload-config` (hot-applies UI colors, no pane restart).

    Herdr's accepted [theme.custom] tokens (from the binary's CustomThemeColors):
        panel_bg, surface0, surface1, surface_dim, overlay0, overlay1,
        text, subtext0, mauve, green, yellow, red, blue, teal, peach, accent
    """

    # TUI app, but the multiplexer also runs on the (GUI-less) linux devbox where
    # its chrome still matters over SSH, so this is NOT gui-only.
    requires_gui = False

    def __init__(self, config_home: Path):
        super().__init__("Herdr", config_home)
        self.config_file = config_home / "herdr/config.toml"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to Herdr by rewriting its [theme] block."""
        if not self.config_file.exists():
            self.log_warning(f"Herdr config not found: {self.config_file}")
            return

        self.log_progress("Updating Herdr theme")

        mat = get_material_colors(theme_data)
        variant = get_theme_variant(theme_data)
        custom = self._map_material_to_herdr(mat, variant)

        self._rewrite_theme_block(custom)
        self._reload_app()

    def _map_material_to_herdr(self, mat: dict, variant: str) -> dict:
        """Map Material Design 3 roles to Herdr's custom theme tokens.

        Surface roles -> Herdr's panel/surface/overlay chrome.
        Accent roles  -> Herdr's named colors. Mirrors apps/ghostty.py's palette
        choices (primary->blue/mauve, tertiary->teal/green, error->red, etc.) so
        the multiplexer and the host terminal read as one coherent theme.
        """
        return {
            # Chrome / surfaces
            "panel_bg": mat.get("surface_container", "#1e1e2e"),
            "surface0": mat.get("surface_container_low", "#313244"),
            "surface1": mat.get("surface_container_high", "#45475a"),
            "surface_dim": mat.get("surface_dim", "#181825"),
            "overlay0": mat.get("outline", "#6c7086"),
            # overlay1 is Herdr's "slightly brighter overlay text" (inactive
            # named tab labels, scroll buttons, "+"). Material outline_variant is
            # a dark hairline/divider tone -> unreadable on the dark surface0, so
            # use on_surface_variant (a readable muted-text tone) instead.
            "overlay1": mat.get("on_surface_variant", "#7f849c"),
            # Text
            "text": mat.get("on_surface", "#cdd6f4"),
            "subtext0": mat.get("on_surface_variant", "#a6adc8"),
            # Accents (align with ghostty.py ANSI mapping)
            "mauve": mat.get("primary", "#cba6f7"),
            "blue": mat.get("primary", "#89b4fa"),
            "teal": mat.get("tertiary", "#94e2d5"),
            "green": mat.get("tertiary", "#a6e3a1"),
            "yellow": mat.get("secondary", "#f9e2af"),
            "peach": mat.get("secondary", "#fab387"),
            "red": mat.get("error", "#f38ba8"),
            # Primary highlight color for borders / nav
            "accent": mat.get("primary", "#89b4fa"),
        }

    def _rewrite_theme_block(self, custom: dict) -> None:
        """Replace the [theme] + [theme.custom] sections in config.toml.

        Preserves every other section (keys, ui, sound, session, ...). Only the
        theme block is regenerated: name set to "custom-dynamic" with a full
        [theme.custom] palette. Idempotent — re-running replaces cleanly.
        """
        content = self.config_file.read_text()
        lines = content.split("\n")
        out: list[str] = []

        # Skip any existing [theme] and [theme.custom] tables; copy everything else.
        skipping = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[theme]") or stripped.startswith("[theme.custom]"):
                skipping = True
                continue
            # A new top-level table that isn't a theme.* table ends the skip.
            if skipping and stripped.startswith("[") and not stripped.startswith(
                "[theme"
            ):
                skipping = False
            if not skipping:
                out.append(line)

        # Build the replacement theme block.
        block = ['[theme]', 'name = "custom-dynamic"', "", "[theme.custom]"]
        for token, value in custom.items():
            block.append(f'{token} = "{value}"')
        block.append("")

        # Insert the theme block at the top, after any leading non-table lines
        # (e.g. `onboarding = false`) so it sits where [theme] originally lived.
        insert_idx = 0
        for i, line in enumerate(out):
            if line.strip().startswith("["):
                insert_idx = i
                break
        else:
            insert_idx = len(out)

        new_lines = out[:insert_idx] + block + out[insert_idx:]
        # Collapse accidental triple blank lines from the splice.
        cleaned: list[str] = []
        for line in new_lines:
            if line == "" and cleaned[-1:] == [""]:
                continue
            cleaned.append(line)

        self.config_file.write_text("\n".join(cleaned))
        self.log_success("Updated Herdr [theme.custom] palette")

    def _reload_app(self) -> None:
        """Hot-reload a running Herdr server so colors apply without restart."""
        if not self.command_exists("herdr"):
            return
        ok = self.run_command(
            ["herdr", "server", "reload-config"],
            error_msg="Could not reload Herdr (run: herdr server reload-config)",
            timeout=5,
        )
        if ok:
            self.log_success("Reloaded running Herdr")
