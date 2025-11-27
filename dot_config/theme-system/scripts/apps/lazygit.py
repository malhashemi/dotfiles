"""lazygit theme generator"""

from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, get_catppuccin_colors, is_dynamic_theme


class LazygitTheme(BaseApp):
    """lazygit (terminal UI for git) theme generator

    Updates the gui.theme section in lazygit's config.yml using surgical YAML editing.
    Preserves comments and user configuration while updating only theme colors.

    Method: Inline surgical swap (ruamel.yaml)
    Reload: None needed (on-demand app - config read on each launch)
    """

    def __init__(self, config_home: Path):
        super().__init__("lazygit", config_home)
        self.config_file = config_home / "lazygit/config.yml"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to lazygit by updating gui.theme section"""

        # Check if config exists
        if not self.config_file.exists():
            self.log_warning(f"Config not found: {self.config_file}")
            self.log_warning("Skipping lazygit theme update")
            return

        self.log_progress("Updating lazygit theme")

        # Generate theme colors based on theme type
        if is_dynamic_theme(theme_data):
            theme_colors = self._generate_dynamic_colors(theme_data)
        else:
            theme_colors = self._generate_static_colors(theme_data)

        # Surgically update gui.theme section in config.yml
        self._update_theme_section(theme_colors)

        self.log_success(f"Updated {self.config_file}")
        # No reload needed - on-demand app

    def _generate_dynamic_colors(self, theme_data: dict) -> dict:
        """Generate theme colors from Material Design 3 palette

        lazygit colors are lists: [color] or [color, modifier]

        Returns:
            Dictionary of lazygit theme keys -> color lists
        """
        mat = get_material_colors(theme_data)

        return {
            "activeBorderColor": [mat.get("primary", "#cba6f7"), "bold"],
            "inactiveBorderColor": [mat.get("outline", "#a6adc8")],
            "searchingActiveBorderColor": [mat.get("secondary", "#f9e2af"), "bold"],
            "optionsTextColor": [mat.get("primary", "#89b4fa")],
            "selectedLineBgColor": [mat.get("surface_container_high", "#313244")],
            "inactiveViewSelectedLineBgColor": [
                mat.get("surface_container", "#45475a")
            ],
            "cherryPickedCommitFgColor": [mat.get("primary", "#89b4fa")],
            "cherryPickedCommitBgColor": [mat.get("primary_container", "#45475a")],
            "markedBaseCommitFgColor": [mat.get("primary", "#89b4fa")],
            "markedBaseCommitBgColor": [mat.get("secondary_container", "#f9e2af")],
            "unstagedChangesColor": [mat.get("error", "#f38ba8")],
            "defaultFgColor": [mat.get("on_surface", "#cdd6f4")],
        }

    def _generate_static_colors(self, theme_data: dict) -> dict:
        """Generate theme colors from Catppuccin palette

        Based on official Catppuccin lazygit themes.
        https://github.com/catppuccin/lazygit

        Returns:
            Dictionary of lazygit theme keys -> color lists
        """
        ctp = get_catppuccin_colors(theme_data)

        return {
            "activeBorderColor": [ctp.get("mauve", "#cba6f7"), "bold"],
            "inactiveBorderColor": [ctp.get("overlay0", "#a6adc8")],
            "searchingActiveBorderColor": [ctp.get("yellow", "#f9e2af"), "bold"],
            "optionsTextColor": [ctp.get("blue", "#89b4fa")],
            "selectedLineBgColor": [ctp.get("surface1", "#313244")],
            "inactiveViewSelectedLineBgColor": [ctp.get("surface0", "#45475a")],
            "cherryPickedCommitFgColor": [ctp.get("blue", "#89b4fa")],
            "cherryPickedCommitBgColor": [ctp.get("surface1", "#45475a")],
            "markedBaseCommitFgColor": [ctp.get("blue", "#89b4fa")],
            "markedBaseCommitBgColor": [ctp.get("yellow", "#f9e2af")],
            "unstagedChangesColor": [ctp.get("red", "#f38ba8")],
            "defaultFgColor": [ctp.get("text", "#cdd6f4")],
        }

    def _update_theme_section(self, theme_colors: dict) -> None:
        """Surgically update gui.theme section in config.yml using ruamel.yaml

        Preserves comments, formatting, and all other configuration sections.
        Only updates theme color values.

        Args:
            theme_colors: Dictionary of theme keys -> color lists
        """
        try:
            from ruamel.yaml import YAML
        except ImportError:
            self.log_error("ruamel.yaml not available")
            self.log_warning("Install with: uv pip install ruamel.yaml")
            return

        yaml = YAML()
        yaml.preserve_quotes = True

        try:
            # Read existing config (preserves comments and formatting)
            with open(self.config_file, "r") as f:
                config = yaml.load(f)

            # Handle empty config file
            if config is None:
                config = {}

            # Ensure gui section exists
            if "gui" not in config:
                config["gui"] = {}

            # Ensure theme section exists
            if "theme" not in config["gui"]:
                config["gui"]["theme"] = {}

            # Surgically update only theme values
            for key, value in theme_colors.items():
                config["gui"]["theme"][key] = value

            # Write back (preserves structure)
            with open(self.config_file, "w") as f:
                yaml.dump(config, f)

        except Exception as e:
            self.log_error(f"Failed to update config: {e}")
