"""Zellij theme generator"""

import subprocess
from pathlib import Path
from .base import BaseApp
from utils import is_dynamic_theme


class ZellijTheme(BaseApp):
    """Zellij terminal multiplexer theme generator

    Delegates to chezmoi templates for theme generation.
    Chezmoi templates read from theme.yaml and generate:
    - config.kdl with theme reference
    - themes/dynamic.kdl with Material colors (for dynamic theme)

    Hot-reload is triggered by chezmoi apply on config.kdl.
    """

    def __init__(self, config_home: Path):
        super().__init__("Zellij", config_home)
        self.zellij_dir = config_home / "zellij"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to Zellij via chezmoi templates"""
        self.log_progress("Applying Zellij theme", emoji="🖥️")

        if not self.command_exists("chezmoi"):
            self.log_warning("chezmoi not found, skipping Zellij")
            return

        # Apply both config and theme files via chezmoi
        # The templates read from theme.yaml which was just updated
        try:
            # Apply dynamic.kdl first (if dynamic theme)
            if is_dynamic_theme(theme_data):
                subprocess.run(
                    [
                        "chezmoi",
                        "apply",
                        "--force",
                        str(self.zellij_dir / "themes/dynamic.kdl"),
                    ],
                    capture_output=True,
                    timeout=10,
                    check=True,
                )

            # Apply config.kdl to trigger hot-reload
            subprocess.run(
                ["chezmoi", "apply", "--force", str(self.zellij_dir / "config.kdl")],
                capture_output=True,
                timeout=10,
                check=True,
            )
            self.log_success("Zellij theme applied (hot-reload triggered)")

        except subprocess.CalledProcessError as e:
            self.log_warning(
                f"chezmoi apply failed: {e.stderr.decode() if e.stderr else e}"
            )
        except subprocess.TimeoutExpired:
            self.log_warning("chezmoi apply timed out")
