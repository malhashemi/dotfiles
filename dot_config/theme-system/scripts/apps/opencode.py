"""OpenCode AI assistant theme integration"""

import json
from pathlib import Path
from .base import BaseApp
from utils import is_dynamic_theme, get_material_colors, get_catppuccin_colors


class OpencodeTheme(BaseApp):
    """OpenCode theme integration

    Generates:
    - Theme files in ~/.config/opencode/themes/ (JSON format)
    - Updates main config's theme reference

    OpenCode watches config and auto-reloads when theme changes.

    Note: We do NOT send signals because production opencode doesn't have
    signal handlers, and unhandled signals terminate the process.
    """

    def __init__(self, config_home: Path):
        super().__init__("OpenCode", config_home)
        self.themes_dir = config_home / "opencode/themes"
        self.config_file = config_home / "opencode/opencode.json"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to OpenCode"""
        if not self.config_file.exists():
            self.log_warning(f"OpenCode config not found: {self.config_file}")
            return

        theme_name = self.generate_theme_file(theme_data)
        self.update_config_reference(theme_name)

    def generate_theme_file(self, theme_data: dict) -> str:
        """Generate theme file in JSON format

        Returns:
            Theme name (filename without .json extension)
        """
        self.log_progress("Generating OpenCode theme")

        if is_dynamic_theme(theme_data):
            content, theme_name = self._generate_dynamic_theme(theme_data)

            # Write to ~/.config/opencode/themes/{theme_name}.json
            self.themes_dir.mkdir(parents=True, exist_ok=True)
            theme_file = self.themes_dir / f"{theme_name}.json"
            self.write_file(theme_file, content)
        else:
            # Static theme: use existing catppuccin-{variant}-mauve file
            variant = theme_data.get("theme", {}).get("name", "mocha")
            theme_name = f"catppuccin-{variant}-mauve"

        return theme_name

    def update_config_reference(self, theme_name: str) -> None:
        """Update theme in main config

        Args:
            theme_name: Name of theme to reference (without .json extension)
        """
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)

            old_theme = config.get("theme", "system")
            config["theme"] = theme_name

            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)

            if old_theme != theme_name:
                self.log_success(f"Updated config: {old_theme} → {theme_name}")
            else:
                self.log_success(f"Theme unchanged: {theme_name}")

        except json.JSONDecodeError as e:
            self.log_error(f"Invalid JSON in config: {e}")
        except Exception as e:
            self.log_error(f"Failed to update config: {e}")

    def _generate_dynamic_theme(self, theme_data: dict) -> tuple[str, str]:
        """Generate JSON for dynamic theme with transparent background

        Returns:
            (json_content, theme_name) tuple
        """
        mat = get_material_colors(theme_data)

        # OpenCode theme with transparent backgrounds
        # Uses Material colors for primary/accent, with Catppuccin Mocha fallbacks
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

        return json.dumps(theme, indent=2), "dynamic"
