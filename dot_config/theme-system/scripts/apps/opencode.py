"""OpenCode AI assistant theme integration"""

import json
import os
import re
import signal
import subprocess
from pathlib import Path
from .base import BaseApp
from utils import is_dynamic_theme, get_material_colors


class OpencodeTheme(BaseApp):
    """OpenCode theme integration.

    OpenCode's TUI resolves a theme by NAME from JSON files in
    ``~/.config/opencode/themes/`` (each file is keyed by its filename). The
    active name is read ONCE at startup from ``tui.json`` (authoritative) with
    ``opencode.json`` as the fallback. The TUI does not watch those files, but
    it DOES re-read every ``themes/*.json`` when it receives ``SIGUSR2`` (its
    theme-refresh handler). It never re-reads the config on any signal.

    So to update colors live — crucially including inside terminal multiplexers
    such as Herdr, which report a fixed built-in palette and do not forward the
    host terminal's color-change notifications (DEC mode 2031 / OSC re-query) —
    we keep the active theme NAME constant (the ``dynamic`` slot) and only ever
    rewrite that slot's CONTENTS, then send ``SIGUSR2``:

    - dynamic theme -> render the slot from the Material Design 3 palette
      (transparent backgrounds so terminal opacity shows through).
    - static theme  -> copy the matching hand-tuned prebuilt theme file
      (``themes/catppuccin-<variant>-mauve.json``) into the slot.

    Because the name never changes, a static<->dynamic switch — which would
    otherwise require a config re-read (i.e. an opencode restart) — reloads
    live exactly like a wallpaper recolor does.
    """

    # The constant theme NAME opencode is always pointed at. We rewrite the
    # file behind this name rather than switching names, because SIGUSR2
    # re-reads theme files but never the config, so the active name must stay
    # fixed for a switch to take effect without a restart.
    SLOT = "dynamic"

    # Lowest opencode version whose TUI handles SIGUSR2 by reloading its themes
    # (verified on 1.17.8). Older builds register no handler and the default
    # disposition for SIGUSR2 would TERMINATE the process, so below this we do
    # not signal — the regenerated slot is then picked up on the next launch.
    SIGUSR2_MIN_VERSION = (1, 17, 8)

    def __init__(self, config_home: Path):
        super().__init__("OpenCode", config_home)
        self.themes_dir = config_home / "opencode/themes"
        self.config_file = config_home / "opencode/opencode.json"
        # The TUI-specific config; since the TUI migration this is the
        # authoritative source for the active theme and overrides opencode.json.
        self.tui_config_file = config_home / "opencode/tui.json"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to OpenCode."""
        if not self.config_file.exists():
            self.log_warning(f"OpenCode config not found: {self.config_file}")
            return

        self.generate_theme_file(theme_data)
        self.update_config_reference()
        self._reload_app()

    # --- slot generation ---------------------------------------------------

    def generate_theme_file(self, theme_data: dict) -> None:
        """(Re)write the single SLOT theme file with the active theme's colors.

        The file is always named ``{SLOT}.json`` regardless of whether a
        dynamic or static theme is active, so opencode's pinned theme name
        never has to change (see the class docstring).
        """
        self.log_progress("Generating OpenCode theme")

        if is_dynamic_theme(theme_data):
            content = self._render_material_slot(theme_data)
        else:
            content = self._render_static_slot(theme_data)

        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.write_file(self.themes_dir / f"{self.SLOT}.json", content)

    def _render_static_slot(self, theme_data: dict) -> str:
        """Populate the slot from the prebuilt static theme file.

        The ``themes/catppuccin-<variant>-mauve.json`` files are hand-tuned and
        chezmoi-managed; the one matching the picked variant is copied verbatim
        into the slot so static picks live-reload through the same path as
        dynamic ones. A new static theme only needs its own prebuilt file under
        the same naming convention. If the prebuilt file is missing (e.g. a
        machine where it has not been applied yet), fall back to deriving the
        slot from the theme's Material palette so opencode still themes.
        """
        variant = theme_data.get("theme", {}).get("name", "mocha")
        source = self.themes_dir / f"catppuccin-{variant}-mauve.json"
        if source.exists():
            return source.read_text()

        self.log_warning(
            f"Prebuilt opencode theme missing ({source.name}); "
            "deriving slot from the Material palette instead"
        )
        return self._render_material_slot(theme_data)

    def _render_material_slot(self, theme_data: dict) -> str:
        """Render the slot JSON from the Material Design 3 palette.

        Uses Material colors for primary/accent roles and Catppuccin Mocha
        defaults for the fixed UI accents, with transparent backgrounds so the
        terminal's opacity shows through.
        """
        mat = get_material_colors(theme_data)

        theme = {
            "$schema": "https://opencode.ai/theme.json",
            "defs": {
                # Material Design colors for accent
                "primary": mat.get("primary", "#cba6f7"),
                "secondary": mat.get("secondary", "#f5c2e7"),
                "accent": mat.get("tertiary", "#cba6f7"),
                "error": mat.get("error", "#f38ba8"),
                # Catppuccin Mocha defaults for UI colors
                "warning": "#f9e2af",
                "success": "#a6e3a1",
                "info": "#94e2d5",
                "text": mat.get("on_surface", "#cdd6f4"),
                "subtext1": "#bac2de",
                "subtext0": "#a6adc8",
                "overlay2": mat.get("outline", "#9399b2"),
                "overlay1": "#7f849c",
                "overlay0": "#6c7086",
                "surface2": mat.get("surface_container_highest", "#585b70"),
                "surface1": mat.get("surface_container_high", "#45475a"),
                "surface0": mat.get("surface_container", "#313244"),
                "mantle": mat.get("surface_container_low", "#181825"),
                "crust": mat.get("surface_container_lowest", "#11111b"),
                "blue": "#89b4fa",
                "sky": "#89dceb",
                "peach": "#fab387",
            },
            "theme": {
                "primary": "primary",
                "secondary": "secondary",
                "accent": "accent",
                "error": "error",
                "warning": "warning",
                "success": "success",
                "info": "info",
                "text": "text",
                "textMuted": "subtext1",
                "background": "none",
                "backgroundPanel": "none",
                "backgroundElement": "surface0",
                "backgroundMenu": "surface1",
                "border": "surface0",
                "borderActive": "surface1",
                "borderSubtle": "surface2",
                "diffAdded": "success",
                "diffRemoved": "error",
                "diffContext": "overlay2",
                "diffHunkHeader": "peach",
                "diffHighlightAdded": "success",
                "diffHighlightRemoved": "error",
                "diffAddedBg": "none",
                "diffRemovedBg": "none",
                "diffContextBg": "none",
                "diffLineNumber": "surface1",
                "diffAddedLineNumberBg": "none",
                "diffRemovedLineNumberBg": "none",
                "markdownText": "text",
                "markdownHeading": "primary",
                "markdownLink": "blue",
                "markdownLinkText": "sky",
                "markdownCode": "success",
                "markdownBlockQuote": "warning",
                "markdownEmph": "warning",
                "markdownStrong": "peach",
                "markdownHorizontalRule": "subtext0",
                "markdownListItem": "primary",
                "markdownListEnumeration": "sky",
                "markdownImage": "blue",
                "markdownImageText": "sky",
                "markdownCodeBlock": "text",
                "syntaxComment": "overlay2",
                "syntaxKeyword": "primary",
                "syntaxFunction": "blue",
                "syntaxVariable": "error",
                "syntaxString": "success",
                "syntaxNumber": "peach",
                "syntaxType": "warning",
                "syntaxOperator": "sky",
                "syntaxPunctuation": "text",
            },
        }

        return json.dumps(theme, indent=2)

    # --- config pointer ----------------------------------------------------

    def update_config_reference(self) -> None:
        """Pin opencode at the constant SLOT in both config files.

        ``tui.json`` is the TUI's authoritative theme source and overrides
        ``opencode.json``; pinning both means a stale ``tui.json`` name can't
        shadow the slot, and machines without a ``tui.json`` still resolve the
        slot via ``opencode.json``. ``tui.json`` is only touched when present
        (we never create it).
        """
        self._pin_theme(self.config_file)
        if self.tui_config_file.exists():
            self._pin_theme(self.tui_config_file)

    def _pin_theme(self, path: Path) -> None:
        """Set ``"theme": SLOT`` in a JSON config file, preserving other keys."""
        try:
            config = json.loads(path.read_text())
            old_theme = config.get("theme")
            if old_theme == self.SLOT:
                self.log_success(f"{path.name}: theme already {self.SLOT}")
                return
            config["theme"] = self.SLOT
            path.write_text(json.dumps(config, indent=2))
            self.log_success(f"{path.name}: theme {old_theme} → {self.SLOT}")
        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON in {path.name}: {e}")
        except OSError as e:
            self.log_error(f"Failed to update {path.name}: {e}")

    # --- live reload -------------------------------------------------------

    def _reload_app(self) -> None:
        """Live-reload running opencode TUIs by sending SIGUSR2.

        opencode's TUI handles SIGUSR2 by re-reading its theme files, so the
        regenerated slot is adopted without a restart. This is the only
        mechanism that works inside terminal multiplexers (e.g. Herdr) that
        don't forward the host terminal's color-change notifications. Gated on
        version so an opencode build without the handler is never signalled
        (it would otherwise be terminated by the default SIGUSR2 action).
        """
        # TRADEOFF (accepted): the SIGUSR2 refresh BOTH re-reads the theme files
        # (what we want — recolors the active `dynamic` file theme) AND calls
        # getPalette() (a burst of OSC color queries). Inside Herdr the cursor
        # query (OSC 12) goes unanswered — a herdr bug; fix submitted as
        # ogulcancelik/herdr#806 — and the desync leaks ESC into opencode's key
        # input → two within 5s hit `session_interrupt` and ABORT that pane's
        # running turn. So this is safe when the pane is idle, but recoloring
        # while an opencode pane is mid-turn aborts that turn. The abort is
        # per-pane (each pane's own getPalette desyncs its own input). Once a
        # herdr build that includes #806 is running, the query completes and
        # there is no abort. Version-gated so a build without the SIGUSR2 handler
        # is never signalled (default SIGUSR2 action would terminate it).
        if not self._supports_sigusr2():
            self.log_warning(
                "Skipping opencode live-reload (opencode missing or older than "
                f"{'.'.join(map(str, self.SIGUSR2_MIN_VERSION))}); "
                "new colors apply on next launch"
            )
            return

        sent = 0
        for pid in self._tui_pids():
            try:
                os.kill(pid, signal.SIGUSR2)
                sent += 1
            except (ProcessLookupError, PermissionError):
                continue

        if sent:
            self.log_success(f"Reloaded {sent} opencode TUI(s) via SIGUSR2")

    def _tui_pids(self) -> list[int]:
        """PIDs of running opencode TUIs.

        Every process named exactly ``opencode`` is a TUI (the server is
        embedded), so an exact-name match never hits an unrelated helper that
        might lack the SIGUSR2 handler.
        """
        try:
            result = subprocess.run(
                ["pgrep", "-x", "opencode"],
                capture_output=True,
                text=True,
                timeout=3,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []
        if result.returncode != 0:
            return []

        pids: list[int] = []
        for token in result.stdout.split():
            try:
                pids.append(int(token))
            except ValueError:
                continue
        return pids

    def _supports_sigusr2(self) -> bool:
        """True when the installed opencode is new enough to handle SIGUSR2."""
        if not self.command_exists("opencode"):
            return False
        try:
            result = subprocess.run(
                ["opencode", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        if result.returncode != 0:
            return False
        return self._parse_version(result.stdout) >= self.SIGUSR2_MIN_VERSION

    @staticmethod
    def _parse_version(text: str) -> tuple[int, int, int]:
        """Extract the first ``MAJOR.MINOR.PATCH`` triple from ``text``."""
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
        if not match:
            return (0, 0, 0)
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
