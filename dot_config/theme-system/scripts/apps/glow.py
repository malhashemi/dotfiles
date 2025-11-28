"""glow markdown viewer theme generator"""

import json
from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, is_dynamic_theme


class GlowTheme(BaseApp):
    """glow markdown viewer theme generator

    Method: external_file (generates glamour JSON style files)
    Reload: None needed (on-demand CLI tool)

    Glow uses glamour library for markdown rendering.
    Theme files are JSON with comprehensive styling for all markdown elements
    plus Chroma syntax highlighting.
    """

    def __init__(self, config_home: Path):
        super().__init__("glow", config_home)
        self.config_file = config_home / "glow/glow.yml"
        self.themes_dir = config_home / "glow/themes"
        self.dynamic_theme = self.themes_dir / "dynamic.json"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to glow"""
        if not self.config_file.exists():
            self.log_warning(f"glow config not found: {self.config_file}")
            return

        self.log_progress("Updating glow theme")

        if is_dynamic_theme(theme_data):
            self._generate_dynamic_theme(theme_data)
            theme_path = str(self.dynamic_theme)
        else:
            # Use pre-installed Catppuccin theme
            variant = theme_data.get("theme", {}).get("name", "mocha")
            theme_path = str(self.themes_dir / f"catppuccin-{variant}.json")

        self._update_config(theme_path)
        self.log_success(f"glow theme: {theme_path}")

    def _generate_dynamic_theme(self, theme_data: dict) -> None:
        """Generate dynamic.json from Material Design 3 colors"""
        mat = get_material_colors(theme_data)
        variant = theme_data.get("theme", {}).get("variant", "dark")
        is_dark = variant != "light"

        # Build glamour style structure
        style = self._build_glamour_style(mat, is_dark)

        self.themes_dir.mkdir(parents=True, exist_ok=True)
        with open(self.dynamic_theme, "w") as f:
            json.dump(style, f, indent=2)
        self.log_success(f"Generated {self.dynamic_theme}")

    def _build_glamour_style(self, mat: dict, is_dark: bool) -> dict:
        """Build complete glamour style JSON from Material Design 3 colors"""
        # Base colors
        fg = mat.get("on_surface", "#cdd6f4")
        bg = mat.get("background", "#1e1e2e")
        surface = mat.get("surface_container", "#313244")
        primary = mat.get("primary", "#cba6f7")
        secondary = mat.get("secondary", "#89b4fa")
        tertiary = mat.get("tertiary", "#a6e3a1")
        error = mat.get("error", "#f38ba8")
        outline = mat.get("outline", "#6c7086")

        return {
            "document": {
                "block_prefix": "\n",
                "block_suffix": "\n",
                "color": fg,
                "margin": 2,
            },
            "block_quote": {"indent": 1, "indent_token": "| ", "color": outline},
            "paragraph": {},
            "list": {"level_indent": 2},
            "heading": {"block_suffix": "\n", "color": fg, "bold": True},
            "h1": {
                "prefix": "# ",
                "color": error,
                "background_color": surface,
                "bold": True,
            },
            "h2": {"prefix": "## ", "color": secondary, "bold": True},
            "h3": {"prefix": "### ", "color": tertiary, "bold": True},
            "h4": {"prefix": "#### ", "color": tertiary},
            "h5": {"prefix": "##### ", "color": primary},
            "h6": {"prefix": "###### ", "color": primary},
            "text": {},
            "strikethrough": {"crossed_out": True},
            "emph": {"italic": True},
            "strong": {"bold": True},
            "hr": {"color": outline, "format": "\n--------\n"},
            "item": {"block_prefix": "* "},
            "enumeration": {"block_prefix": ". "},
            "task": {"ticked": "[x] ", "unticked": "[ ] "},
            "link": {"color": primary, "underline": True},
            "link_text": {"color": secondary, "bold": True},
            "image": {"color": primary, "underline": True},
            "image_text": {"color": secondary, "format": "Image: {{.text}}"},
            "code": {
                "prefix": " ",
                "suffix": " ",
                "color": tertiary,
                "background_color": surface,
            },
            "code_block": {
                "color": fg,
                "margin": 2,
                "chroma": self._build_chroma_style(mat),
            },
            "table": {
                "center_separator": "+",
                "column_separator": "|",
                "row_separator": "-",
            },
            "definition_list": {},
            "definition_term": {"bold": True},
            "definition_description": {"block_prefix": "\n> "},
            "html_block": {},
            "html_span": {},
        }

    def _build_chroma_style(self, mat: dict) -> dict:
        """Build Chroma syntax highlighting style"""
        fg = mat.get("on_surface", "#cdd6f4")
        bg = mat.get("surface_container", "#313244")
        primary = mat.get("primary", "#cba6f7")
        secondary = mat.get("secondary", "#89b4fa")
        tertiary = mat.get("tertiary", "#a6e3a1")
        error = mat.get("error", "#f38ba8")
        outline = mat.get("outline", "#6c7086")

        return {
            "text": {"color": fg},
            "error": {"color": fg, "background_color": error},
            "comment": {"color": outline},
            "comment_preproc": {"color": secondary},
            "keyword": {"color": primary},
            "keyword_reserved": {"color": primary},
            "keyword_namespace": {"color": tertiary},
            "keyword_type": {"color": tertiary},
            "operator": {"color": secondary},
            "punctuation": {"color": outline},
            "name": {"color": fg},
            "name_builtin": {"color": secondary},
            "name_tag": {"color": primary},
            "name_attribute": {"color": tertiary},
            "name_class": {"color": tertiary},
            "name_constant": {"color": tertiary},
            "name_decorator": {"color": primary},
            "name_exception": {"color": error},
            "name_function": {"color": secondary},
            "name_other": {"color": fg},
            "literal": {"color": fg},
            "literal_number": {"color": secondary},
            "literal_date": {"color": secondary},
            "literal_string": {"color": tertiary},
            "literal_string_escape": {"color": primary},
            "generic_deleted": {"color": error},
            "generic_emph": {"color": fg, "italic": True},
            "generic_inserted": {"color": tertiary},
            "generic_strong": {"color": fg, "bold": True},
            "generic_subheading": {"color": secondary},
            "background": {"background_color": bg},
        }

    def _update_config(self, theme_path: str) -> None:
        """Update glow.yml with theme reference"""
        try:
            from ruamel.yaml import YAML

            yaml = YAML()
            yaml.preserve_quotes = True

            with open(self.config_file, "r") as f:
                config = yaml.load(f) or {}

            old_style = config.get("style", "auto")
            config["style"] = theme_path

            with open(self.config_file, "w") as f:
                yaml.dump(config, f)

            if old_style != theme_path:
                self.log_success(f'Updated glow: style = "{theme_path}"')
            else:
                self.log_success(f'glow style unchanged: "{theme_path}"')

        except ImportError:
            # Fallback: regex replacement
            import re

            with open(self.config_file, "r") as f:
                content = f.read()

            if "style:" in content:
                content = re.sub(
                    r"^style:.*$", f'style: "{theme_path}"', content, flags=re.MULTILINE
                )
            else:
                content = f'style: "{theme_path}"\n' + content

            with open(self.config_file, "w") as f:
                f.write(content)
