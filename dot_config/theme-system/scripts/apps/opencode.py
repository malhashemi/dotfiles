"""OpenCode AI assistant theme integration"""

import json
from pathlib import Path
from .base import BaseApp
from utils import is_dynamic_theme


class OpencodeTheme(BaseApp):
    """OpenCode theme integration

    Method: Updates config file. OpenCode watches config and auto-reloads.

    Note: We do NOT send signals because production opencode doesn't have
    signal handlers, and unhandled signals terminate the process.

    Theme selection:
    - Dynamic theme → use "dynamic" (chezmoi-templated theme with transparent bg)
    - Static theme → use corresponding catppuccin-{variant}-mauve theme
    """

    def __init__(self, config_home: Path):
        super().__init__("OpenCode", config_home)
        self.config_file = config_home / "opencode/opencode.json"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to OpenCode by updating config reference"""
        if not self.config_file.exists():
            self.log_warning(f"OpenCode config not found: {self.config_file}")
            return

        self.log_progress("Updating OpenCode theme")

        if is_dynamic_theme(theme_data):
            # Dynamic theme: use chezmoi-templated theme with transparent background
            # This works on headless environments where "system" theme fails
            theme_name = "dynamic"
        else:
            # Static theme: use corresponding Catppuccin theme file
            variant = theme_data.get("theme", {}).get("name", "mocha")
            theme_name = f"catppuccin-{variant}-mauve"

        self._update_config(theme_name)

    def _update_config(self, theme_name: str) -> None:
        """Update opencode.json with theme reference"""
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)

            old_theme = config.get("theme", "system")
            config["theme"] = theme_name

            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)

            if old_theme != theme_name:
                self.log_success(f'Updated OpenCode: theme = "{theme_name}"')
            else:
                self.log_success(f'OpenCode theme unchanged: "{theme_name}"')

        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON in OpenCode config: {e}")
        except Exception as e:
            self.log_error(f"Failed to update OpenCode config: {e}")
