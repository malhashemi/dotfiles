"""OpenCode AI assistant theme integration"""

import json
from pathlib import Path
from .base import BaseApp
from utils import is_dynamic_theme


class OpencodeTheme(BaseApp):
    """OpenCode theme integration

    Method: config reference update
    Reload: manual (requires restart or /theme command in TUI)

    Simple integration:
    - Dynamic theme → set to "system" (inherits terminal colors from WezTerm)
    - Static theme → set to corresponding catppuccin-{variant}-mauve theme
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
            # Dynamic theme: use "system" to inherit terminal colors
            theme_name = "system"
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
                self.log_warning("Restart opencode or use /theme command to apply")
            else:
                self.log_success(f'OpenCode theme unchanged: "{theme_name}"')

        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON in OpenCode config: {e}")
        except Exception as e:
            self.log_error(f"Failed to update OpenCode config: {e}")
