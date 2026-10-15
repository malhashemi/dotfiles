"""Publish the desktop palette through T3 Code's environment theme interface."""

import json
import os
import shutil
import tempfile
from pathlib import Path

from .base import BaseApp
from utils import get_material_colors


class T3CodeTheme(BaseApp):
    """One stable theme slot, refreshed live on desktop and server web clients.

    Keep this enabled on headless hosts: their connected web clients also use
    environment themes. The CLI validates and atomically publishes the file,
    then sets the default even if a client has manually picked another theme.
    Client preferences (including glass opacity) remain owned by T3 settings.
    """

    SLOT = "theme-system"

    def __init__(self, config_home: Path):
        super().__init__("T3 Code", config_home)
        self.base_dir = Path(os.environ.get("T3CODE_HOME", str(Path.home() / ".t3"))).expanduser()

    def apply_theme(self, theme_data: dict) -> None:
        # Do not provision T3 state on machines where it has never been used.
        if not (self.base_dir / "userdata").is_dir():
            return

        cli = shutil.which("t3")
        if cli is None:
            local_cli = Path.home() / ".local/bin/t3"
            if local_cli.is_file() and os.access(local_cli, os.X_OK):
                cli = str(local_cli)
        if cli is None:
            self.log_warning("T3 CLI not found; skipping theme")
            return

        mat = get_material_colors(theme_data)
        theme = theme_data["theme"]
        colors = theme.get("colors", {})
        palette = {
            "name": "Theme System",
            "appearance": "light" if theme.get("variant") == "light" else "dark",
            "canvas": mat["background"],
            "accent": mat["primary"],
            "colors": {
                "text": mat["on_surface"],
                "textMuted": mat["on_surface_variant"],
                "surface": mat["surface_container_low"],
                "surfaceRaised": mat["surface_container"],
                "surfaceOverlay": mat["surface_container_high"],
                "border": mat["outline_variant"],
                "accentForeground": mat["on_primary"],
                "codeBackground": mat["surface_container_lowest"],
                "codeForeground": mat["on_surface"],
                "sidebar": mat["surface_container_lowest"],
                "sidebarForeground": mat["on_surface"],
                "sidebarBorder": mat["outline_variant"],
                "terminalBackground": mat["surface"],
                "terminalForeground": mat["on_surface"],
                "terminalCursor": mat["primary"],
                "terminalSelection": mat["surface_container_highest"],
                "error": mat["error"],
                "warning": colors.get("yellow", mat["tertiary"]),
            },
        }

        self.log_progress("Updating T3 Code theme")
        with tempfile.TemporaryDirectory(prefix="t3-theme-") as temp_dir:
            source = Path(temp_dir) / f"{self.SLOT}.json"
            source.write_text(json.dumps(palette, indent=2) + "\n")
            if self.run_command(
                [cli, "theme", "set", str(source), "--id", self.SLOT,
                 "--base-dir", str(self.base_dir)],
                error_msg="Could not publish T3 Code theme (requires a CLI with `t3 theme set`)",
                timeout=10,
            ):
                self.log_success("T3 Code theme published; connected clients update live")
