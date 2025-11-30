"""OpenCode AI assistant theme integration"""

import json
from pathlib import Path
from .base import BaseApp
from utils import is_dynamic_theme, get_material_colors, get_catppuccin_colors


class OpencodeTheme(BaseApp):
    """OpenCode theme integration

    Method: Generates theme files and updates config. OpenCode watches config
    and auto-reloads.

    Note: We do NOT send signals because production opencode doesn't have
    signal handlers, and unhandled signals terminate the process.

    Theme selection:
    - Dynamic theme → generate dynamic.json with transparent background
    - Static theme → use corresponding catppuccin-{variant}-mauve theme
    """

    def __init__(self, config_home: Path):
        super().__init__("OpenCode", config_home)
        self.config_file = config_home / "opencode/opencode.json"
        self.themes_dir = config_home / "opencode/themes"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to OpenCode by generating theme file and updating config"""
        if not self.config_file.exists():
            self.log_warning(f"OpenCode config not found: {self.config_file}")
            return

        self.log_progress("Updating OpenCode theme")

        if is_dynamic_theme(theme_data):
            # Dynamic theme: generate theme file with transparent background
            self._generate_dynamic_theme(theme_data)
            theme_name = "dynamic"
        else:
            # Static theme: use corresponding Catppuccin theme file
            variant = theme_data.get("theme", {}).get("name", "mocha")
            theme_name = f"catppuccin-{variant}-mauve"

        self._update_config(theme_name)

    def _generate_dynamic_theme(self, theme_data: dict) -> None:
        """Generate dynamic.json theme file with transparent background"""
        mat = get_material_colors(theme_data)
        ctp = get_catppuccin_colors(theme_data)

        # Build theme with transparent backgrounds
        theme = {
            "$schema": "https://opencode.ai/theme.json",
            "defs": {
                "primary": mat.get("primary", ctp.get("mauve", "#cba6f7")),
                "secondary": mat.get("secondary", ctp.get("pink", "#f5c2e7")),
                "accent": mat.get("tertiary", ctp.get("mauve", "#cba6f7")),
                "error": mat.get("error", ctp.get("red", "#f38ba8")),
                "warning": ctp.get("yellow", "#f9e2af"),
                "success": ctp.get("green", "#a6e3a1"),
                "info": ctp.get("teal", "#94e2d5"),
                "text": ctp.get("text", "#cdd6f4"),
                "subtext1": ctp.get("subtext1", "#bac2de"),
                "subtext0": ctp.get("subtext0", "#a6adc8"),
                "overlay2": ctp.get("overlay2", "#9399b2"),
                "overlay1": ctp.get("overlay1", "#7f849c"),
                "overlay0": ctp.get("overlay0", "#6c7086"),
                "surface2": ctp.get("surface2", "#585b70"),
                "surface1": ctp.get("surface1", "#45475a"),
                "surface0": ctp.get("surface0", "#313244"),
                "mantle": ctp.get("mantle", "#181825"),
                "crust": ctp.get("crust", "#11111b"),
                "blue": ctp.get("blue", "#89b4fa"),
                "sky": ctp.get("sky", "#89dceb"),
                "peach": ctp.get("peach", "#fab387"),
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

        # Ensure themes directory exists
        self.themes_dir.mkdir(parents=True, exist_ok=True)

        # Write theme file
        theme_file = self.themes_dir / "dynamic.json"
        self.write_file(theme_file, json.dumps(theme, indent=2))

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
