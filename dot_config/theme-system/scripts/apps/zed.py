"""Zed editor theme integration"""

import json
import re
from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, is_dynamic_theme


class ZedTheme(BaseApp):
    """Zed editor theme integration

    Method: hybrid (builtin for static, external_file for dynamic)
    Reload: automatic (Zed watches settings.json)

    Static themes: Update theme.dark/light references to Catppuccin variants
    Dynamic themes: Generate themes/dynamic.json and update reference
    """

    # GUI-only app - skip on headless systems
    requires_gui = True

    def __init__(self, config_home: Path):
        super().__init__("Zed", config_home)
        self.config_file = config_home / "zed/settings.json"
        self.themes_dir = config_home / "zed/themes"
        self.dynamic_theme = self.themes_dir / "dynamic.json"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to Zed"""
        if not self.config_file.exists():
            self.log_warning(f"Zed config not found: {self.config_file}")
            return

        self.log_progress("Updating Zed theme")

        if is_dynamic_theme(theme_data):
            self._generate_dynamic_theme(theme_data)
            dark_theme = "Dynamic"
            light_theme = "Dynamic"
        else:
            variant = theme_data.get("theme", {}).get("name", "mocha")
            dark_theme = f"Catppuccin {variant.title()}"
            light_theme = "Catppuccin Latte"  # Always Latte for light mode

        self._update_config(dark_theme, light_theme)

    def _generate_dynamic_theme(self, theme_data: dict) -> None:
        """Generate dynamic.json from Material Design 3 colors"""
        mat = get_material_colors(theme_data)

        # Determine appearance based on theme variant
        variant = theme_data.get("theme", {}).get("variant", "dark")
        appearance = "light" if variant == "light" else "dark"

        theme_content = {
            "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
            "name": "Dynamic",
            "author": "Theme System",
            "themes": [
                {
                    "name": "Dynamic",
                    "appearance": appearance,
                    "style": self._build_style(mat, appearance),
                }
            ],
        }

        self.themes_dir.mkdir(parents=True, exist_ok=True)

        with open(self.dynamic_theme, "w") as f:
            json.dump(theme_content, f, indent=2)

        self.log_success(f"Generated {self.dynamic_theme}")
        self.log_warning("Restart Zed to apply dynamic theme")

    def _build_style(self, mat: dict, appearance: str) -> dict:
        """Build Zed style object from Material Design 3 colors"""
        return {
            # Background colors
            "background": mat.get("background", "#1e1e2e"),
            "surface.background": mat.get("surface", "#1e1e2e"),
            "elevated_surface.background": mat.get("surface_container", "#313244"),
            "element.background": mat.get("surface_container_low", "#181825"),
            "element.hover": mat.get("surface_container_high", "#45475a"),
            "element.selected": mat.get("surface_container_highest", "#585b70"),
            "ghost_element.hover": mat.get("surface_container", "#313244"),
            "ghost_element.selected": mat.get("surface_container_high", "#45475a"),
            # Text colors
            "text": mat.get("on_surface", "#cdd6f4"),
            "text.muted": mat.get("outline", "#6c7086"),
            "text.accent": mat.get("primary", "#cba6f7"),
            # Border colors
            "border": mat.get("outline", "#45475a"),
            "border.variant": mat.get("surface_container", "#313244"),
            # Editor colors
            "editor.background": mat.get("surface", "#1e1e2e"),
            "editor.gutter.background": mat.get("surface", "#1e1e2e"),
            "editor.line_number": mat.get("outline", "#6c7086"),
            "editor.active_line.background": mat.get(
                "surface_container_low", "#181825"
            ),
            # Syntax highlighting
            "syntax": {
                "keyword": {"color": mat.get("primary", "#cba6f7")},
                "function": {"color": mat.get("secondary", "#89b4fa")},
                "string": {"color": mat.get("tertiary", "#a6e3a1")},
                "comment": {
                    "color": mat.get("outline", "#6c7086"),
                    "font_style": "italic",
                },
                "number": {"color": mat.get("secondary", "#fab387")},
                "type": {"color": mat.get("tertiary", "#f9e2af")},
                "variable": {"color": mat.get("on_surface", "#cdd6f4")},
                "constant": {"color": mat.get("secondary", "#fab387")},
            },
            # Terminal colors
            "terminal.background": mat.get("surface", "#1e1e2e"),
            "terminal.foreground": mat.get("on_surface", "#cdd6f4"),
            "terminal.ansi.black": mat.get("surface_container", "#45475a"),
            "terminal.ansi.red": mat.get("error", "#f38ba8"),
            "terminal.ansi.green": mat.get("tertiary", "#a6e3a1"),
            "terminal.ansi.yellow": mat.get("secondary", "#f9e2af"),
            "terminal.ansi.blue": mat.get("primary", "#89b4fa"),
            "terminal.ansi.magenta": mat.get("primary", "#cba6f7"),
            "terminal.ansi.cyan": mat.get("tertiary", "#94e2d5"),
            "terminal.ansi.white": mat.get("on_surface", "#bac2de"),
            "terminal.ansi.bright_black": mat.get("outline", "#6c7086"),
            "terminal.ansi.bright_red": mat.get("error", "#f38ba8"),
            "terminal.ansi.bright_green": mat.get("tertiary", "#a6e3a1"),
            "terminal.ansi.bright_yellow": mat.get("secondary", "#f9e2af"),
            "terminal.ansi.bright_blue": mat.get("primary", "#89b4fa"),
            "terminal.ansi.bright_magenta": mat.get("primary", "#cba6f7"),
            "terminal.ansi.bright_cyan": mat.get("tertiary", "#94e2d5"),
            "terminal.ansi.bright_white": mat.get("on_surface", "#a6adc8"),
        }

    def _update_config(self, dark_theme: str, light_theme: str) -> None:
        """Update settings.json theme refs IN PLACE, preserving comments/layout.

        Zed settings are JSONC (comments + trailing commas). We parse a sanitized
        copy only to read the current values, then patch the `theme`/`icon_theme`
        values in the raw text so the user's comments and formatting survive.
        """
        try:
            raw = self.config_file.read_text()

            try:
                config = json.loads(self._jsonc_to_json(raw))
            except json.JSONDecodeError as e:
                self.log_error(f"Invalid JSON in Zed config: {e}")
                return

            old = config.get("theme")
            if isinstance(old, dict):
                old_dark, old_light = old.get("dark", ""), old.get("light", "")
                mode = old.get("mode") or "system"
            else:
                old_dark = old_light = old or ""
                mode = "system"

            theme_obj = (
                "{\n"
                f'    "mode": "{mode}",\n'
                f'    "light": "{light_theme}",\n'
                f'    "dark": "{dark_theme}"\n'
                "  }"
            )

            new = self._set_key(raw, "theme", theme_obj)
            if "Catppuccin" in dark_theme:  # sync icon theme for Catppuccin only
                new = self._set_key(new, "icon_theme", json.dumps(dark_theme))

            if new != raw:
                self.config_file.write_text(new)

            if old_dark != dark_theme or old_light != light_theme:
                self.log_success(
                    f'Updated Zed: dark="{dark_theme}", light="{light_theme}"'
                )
            else:
                self.log_success("Zed theme unchanged")

        except Exception as e:
            self.log_error(f"Failed to update Zed config: {e}")

    @staticmethod
    def _jsonc_to_json(text: str) -> str:
        """Strip // and /* */ comments (string-aware) and trailing commas."""
        out = []
        i, n, in_str = 0, len(text), False
        while i < n:
            c = text[i]
            if in_str:
                out.append(c)
                if c == "\\" and i + 1 < n:
                    out.append(text[i + 1])
                    i += 2
                    continue
                if c == '"':
                    in_str = False
                i += 1
                continue
            if c == '"':
                in_str = True
                out.append(c)
                i += 1
                continue
            if c == "/" and i + 1 < n and text[i + 1] == "/":
                while i < n and text[i] != "\n":
                    i += 1
                continue
            if c == "/" and i + 1 < n and text[i + 1] == "*":
                i += 2
                while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                    i += 1
                i += 2
                continue
            out.append(c)
            i += 1
        return re.sub(r",(\s*[}\]])", r"\1", "".join(out))

    @staticmethod
    def _set_key(text: str, key: str, value_json: str) -> str:
        """Replace `"key": <value>` (string/flat object/array/scalar) in raw
        JSONC text, preserving everything else. Inserts after the root brace if
        the key is absent."""
        pat = re.compile(
            r'("' + re.escape(key) + r'"\s*:\s*)'
            r'(\{[^{}]*\}|\[[^\[\]]*\]|"(?:[^"\\]|\\.)*"|true|false|null|-?[\d.]+)'
        )
        if pat.search(text):
            return pat.sub(lambda m: m.group(1) + value_json, text, count=1)
        return re.sub(r"\{", '{\n  "' + key + '": ' + value_json + ",", text, count=1)
