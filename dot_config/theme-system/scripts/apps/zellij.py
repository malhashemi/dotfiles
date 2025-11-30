"""Zellij theme generator"""

import subprocess
from pathlib import Path
from .base import BaseApp
from utils import is_dynamic_theme


class ZellijTheme(BaseApp):
    """Zellij terminal multiplexer theme generator

    Uses chezmoi templates with INLINE theme definition for hot-reload.

    Key insight from Zellij docs:
    - Theme files in themes/ directory are NOT watched (loaded at startup only)
    - Themes defined INLINE in config.kdl ARE hot-reloaded when config changes

    The config.kdl.tmpl template includes the dynamic theme colors inline,
    so when theme.yaml changes, chezmoi regenerates config.kdl with new colors,
    and Zellij's file watcher detects the change and hot-reloads.
    """

    def __init__(self, config_home: Path):
        super().__init__("Zellij", config_home)
        self.config_file = config_home / "zellij/config.kdl"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to Zellij via chezmoi template regeneration"""
        self.log_progress("Applying Zellij theme", emoji="🖥️")

        if not self.command_exists("chezmoi"):
            self.log_warning("chezmoi not found, skipping Zellij")
            return

        # Regenerate config.kdl from template
        # The template reads theme.yaml and embeds colors inline
        # This triggers Zellij's file watcher for hot-reload
        try:
            result = subprocess.run(
                ["chezmoi", "apply", "--force", str(self.config_file)],
                capture_output=True,
                timeout=10,
            )

            if result.returncode == 0:
                theme_name = theme_data.get("theme", {}).get("name", "unknown")
                self.log_success(f"Zellij config regenerated ({theme_name} theme)")
            else:
                stderr = result.stderr.decode() if result.stderr else "unknown error"
                self.log_warning(f"chezmoi apply failed: {stderr}")

        except subprocess.TimeoutExpired:
            self.log_warning("chezmoi apply timed out")
        except Exception as e:
            self.log_warning(f"Zellij theme apply failed: {e}")
