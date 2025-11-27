"""OpenCode AI assistant theme generator"""

import json
from pathlib import Path
from .base import BaseApp
from utils import (
    get_material_colors,
    get_catppuccin_colors,
    is_dynamic_theme,
    get_theme_variant,
)


class OpencodeTheme(BaseApp):
    """OpenCode theme generator

    Method: hybrid (external_file for static + dynamic)
    Reload: manual (requires restart or /theme command in TUI)

    OpenCode is an AI coding assistant TUI with excellent theme support.
    Static themes: use existing catppuccin-{variant}-mauve.json files
    Dynamic themes: generate themes/dynamic.json with MD3 colors
    """

    def __init__(self, config_home: Path):
        super().__init__("OpenCode", config_home)
        self.config_file = config_home / "opencode/opencode.json"
        self.themes_dir = config_home / "opencode/themes"
        self.dynamic_theme = self.themes_dir / "dynamic.json"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to OpenCode

        For static themes: update config to reference catppuccin-{variant}-mauve
        For dynamic themes: generate dynamic.json and update config reference
        """
        if not self.config_file.exists():
            self.log_warning(f"OpenCode config not found: {self.config_file}")
            return

        self.log_progress("Updating OpenCode theme")

        if is_dynamic_theme(theme_data):
            # Generate dynamic theme file
            self._generate_dynamic_theme(theme_data)
            theme_name = "dynamic"
        else:
            # Use existing Catppuccin theme
            variant = theme_data.get("theme", {}).get("name", "mocha")
            theme_name = f"catppuccin-{variant}-mauve"

            # Verify theme file exists
            theme_file = self.themes_dir / f"{theme_name}.json"
            if not theme_file.exists():
                self.log_warning(
                    f"Theme file not found: {theme_file}, using builtin catppuccin"
                )
                theme_name = "catppuccin"

        self._update_config(theme_name)

    def _generate_dynamic_theme(self, theme_data: dict) -> None:
        """Generate dynamic.json from Material Design 3 colors

        OpenCode has 50+ semantic color keys organized into categories:
        - General: primary, secondary, accent, error, warning, success, info
        - Text: text, textMuted
        - Background: background, backgroundPanel, backgroundElement
        - Border: border, borderActive, borderSubtle
        - Diff: diffAdded, diffRemoved, diffContext, etc.
        - Markdown: markdownHeading, markdownCode, etc.
        - Syntax: syntaxKeyword, syntaxFunction, etc.
        """
        mat = get_material_colors(theme_data)
        variant = get_theme_variant(theme_data)

        # Generate diff background colors based on light/dark mode
        if variant == "light":
            diff_added_bg = "#d6f0d9"  # Light green
            diff_removed_bg = "#f6dfe2"  # Light red
            diff_added_line_bg = "#c9e3cb"
            diff_removed_line_bg = "#e9d3d6"
        else:
            diff_added_bg = "#24312b"  # Dark green
            diff_removed_bg = "#3c2a32"  # Dark red
            diff_added_line_bg = "#1e2a25"
            diff_removed_line_bg = "#32232a"

        theme = {
            "$schema": "https://opencode.ai/theme.json",
            "defs": {
                # Primary colors
                "primary": mat.get("primary", "#cba6f7"),
                "secondary": mat.get("secondary", "#89b4fa"),
                "tertiary": mat.get("tertiary", "#a6e3a1"),
                "error": mat.get("error", "#f38ba8"),
                # Surface colors
                "background": mat.get("background", "#1e1e2e"),
                "surface": mat.get("surface", "#1e1e2e"),
                "surfaceContainer": mat.get("surface_container", "#313244"),
                "surfaceContainerHigh": mat.get("surface_container_high", "#45475a"),
                "surfaceContainerLow": mat.get("surface_container_low", "#181825"),
                # Text colors
                "onSurface": mat.get("on_surface", "#cdd6f4"),
                "onSurfaceVariant": mat.get("on_surface_variant", "#a6adc8"),
                "outline": mat.get("outline", "#6c7086"),
                "outlineVariant": mat.get("outline_variant", "#45475a"),
                # Diff background colors
                "diffAddedBg": diff_added_bg,
                "diffRemovedBg": diff_removed_bg,
                "diffAddedLineNumberBg": diff_added_line_bg,
                "diffRemovedLineNumberBg": diff_removed_line_bg,
            },
            "theme": {
                # General
                "primary": {"dark": "primary", "light": "primary"},
                "secondary": {"dark": "secondary", "light": "secondary"},
                "accent": {"dark": "tertiary", "light": "tertiary"},
                "error": {"dark": "error", "light": "error"},
                "warning": {"dark": "secondary", "light": "secondary"},
                "success": {"dark": "tertiary", "light": "tertiary"},
                "info": {"dark": "tertiary", "light": "tertiary"},
                # Text
                "text": {"dark": "onSurface", "light": "onSurface"},
                "textMuted": {"dark": "onSurfaceVariant", "light": "onSurfaceVariant"},
                # Background
                "background": {"dark": "background", "light": "background"},
                "backgroundPanel": {"dark": "surface", "light": "surface"},
                "backgroundElement": {
                    "dark": "surfaceContainer",
                    "light": "surfaceContainer",
                },
                # Border
                "border": {"dark": "outlineVariant", "light": "outlineVariant"},
                "borderActive": {"dark": "outline", "light": "outline"},
                "borderSubtle": {
                    "dark": "surfaceContainer",
                    "light": "surfaceContainer",
                },
                # Diff colors
                "diffAdded": {"dark": "tertiary", "light": "tertiary"},
                "diffRemoved": {"dark": "error", "light": "error"},
                "diffContext": {"dark": "outline", "light": "outline"},
                "diffHunkHeader": {"dark": "secondary", "light": "secondary"},
                "diffHighlightAdded": {"dark": "tertiary", "light": "tertiary"},
                "diffHighlightRemoved": {"dark": "error", "light": "error"},
                "diffAddedBg": {"dark": "diffAddedBg", "light": "diffAddedBg"},
                "diffRemovedBg": {"dark": "diffRemovedBg", "light": "diffRemovedBg"},
                "diffContextBg": {"dark": "surface", "light": "surface"},
                "diffLineNumber": {"dark": "outlineVariant", "light": "outlineVariant"},
                "diffAddedLineNumberBg": {
                    "dark": "diffAddedLineNumberBg",
                    "light": "diffAddedLineNumberBg",
                },
                "diffRemovedLineNumberBg": {
                    "dark": "diffRemovedLineNumberBg",
                    "light": "diffRemovedLineNumberBg",
                },
                # Markdown
                "markdownText": {"dark": "onSurface", "light": "onSurface"},
                "markdownHeading": {"dark": "primary", "light": "primary"},
                "markdownLink": {"dark": "secondary", "light": "secondary"},
                "markdownLinkText": {"dark": "tertiary", "light": "tertiary"},
                "markdownCode": {"dark": "tertiary", "light": "tertiary"},
                "markdownBlockQuote": {"dark": "secondary", "light": "secondary"},
                "markdownEmph": {"dark": "secondary", "light": "secondary"},
                "markdownStrong": {"dark": "primary", "light": "primary"},
                "markdownHorizontalRule": {"dark": "outline", "light": "outline"},
                "markdownListItem": {"dark": "primary", "light": "primary"},
                "markdownListEnumeration": {"dark": "tertiary", "light": "tertiary"},
                "markdownImage": {"dark": "secondary", "light": "secondary"},
                "markdownImageText": {"dark": "tertiary", "light": "tertiary"},
                "markdownCodeBlock": {"dark": "onSurface", "light": "onSurface"},
                # Syntax highlighting
                "syntaxComment": {"dark": "outline", "light": "outline"},
                "syntaxKeyword": {"dark": "primary", "light": "primary"},
                "syntaxFunction": {"dark": "secondary", "light": "secondary"},
                "syntaxVariable": {"dark": "error", "light": "error"},
                "syntaxString": {"dark": "tertiary", "light": "tertiary"},
                "syntaxNumber": {"dark": "secondary", "light": "secondary"},
                "syntaxType": {"dark": "secondary", "light": "secondary"},
                "syntaxOperator": {"dark": "tertiary", "light": "tertiary"},
                "syntaxPunctuation": {"dark": "onSurface", "light": "onSurface"},
            },
        }

        # Ensure themes directory exists
        self.themes_dir.mkdir(parents=True, exist_ok=True)

        with open(self.dynamic_theme, "w") as f:
            json.dump(theme, f, indent=2)

        self.log_success(f"Generated {self.dynamic_theme}")

    def _update_config(self, theme_name: str) -> None:
        """Update opencode.json with theme reference

        Surgically updates only the theme key, preserving all other config.
        """
        try:
            with open(self.config_file, "r") as f:
                config = json.load(f)

            # Update theme reference
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
