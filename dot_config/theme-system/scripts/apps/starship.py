"""Starship prompt theme generator"""

from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, get_catppuccin_colors, is_dynamic_theme


class StarshipTheme(BaseApp):
    """Starship prompt theme generator

    Method: inline (surgical TOML swap via tomlkit)
    Reload: Instant (config read on every prompt)

    Design decisions:
    - Dynamic palette named "dynamic"
    - Static palettes named "catppuccin_{variant}"
    - Clean approach: remove ALL old palettes on each switch

    Starship's native palette system (`palette = "name"` + `[palettes.name]`)
    aligns perfectly with our theming approach. Config is re-read on every
    prompt render, so changes appear instantly without restart.
    """

    def __init__(self, config_home: Path):
        super().__init__("Starship", config_home)
        self.config_file = config_home / "starship/starship.toml"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to Starship

        Updates starship.toml with new palette reference and colors.
        Removes all existing palettes for clean switching.
        """
        if not self.config_file.exists():
            self.log_warning(f"Starship config not found: {self.config_file}")
            return

        self.log_progress("Updating Starship theme")

        if is_dynamic_theme(theme_data):
            palette_name = "dynamic"
            palette_colors = self._generate_dynamic_palette(theme_data)
        else:
            variant = theme_data.get("theme", {}).get("name", "mocha")
            palette_name = f"catppuccin_{variant}"
            palette_colors = self._generate_static_palette(theme_data)

        self._update_config(palette_name, palette_colors)

    def _generate_dynamic_palette(self, theme_data: dict) -> dict:
        """Generate palette from Material Design 3 colors

        Maps MD3 semantic colors to Catppuccin-style names for consistency
        with existing starship module styles that reference colors like
        'mauve', 'green', 'text', etc.

        Returns:
            Dict with 26 color keys mapping to hex values
        """
        mat = get_material_colors(theme_data)

        return {
            "rosewater": mat.get("primary_fixed_dim", "#f5e0dc"),
            "flamingo": mat.get("error_container", "#f2cdcd"),
            "pink": mat.get("tertiary_fixed", "#f5c2e7"),
            "mauve": mat.get("primary", "#cba6f7"),
            "red": mat.get("error", "#f38ba8"),
            "maroon": mat.get("error", "#eba0ac"),
            "peach": mat.get("secondary", "#fab387"),
            "yellow": mat.get("tertiary", "#f9e2af"),
            "green": mat.get("tertiary", "#a6e3a1"),
            "teal": mat.get("tertiary_container", "#94e2d5"),
            "sky": mat.get("secondary_fixed", "#89dceb"),
            "sapphire": mat.get("primary_container", "#74c7ec"),
            "blue": mat.get("primary", "#89b4fa"),
            "lavender": mat.get("secondary", "#b4befe"),
            "text": mat.get("on_surface", "#cdd6f4"),
            "subtext1": mat.get("on_surface_variant", "#bac2de"),
            "subtext0": mat.get("outline", "#a6adc8"),
            "overlay2": mat.get("outline_variant", "#9399b2"),
            "overlay1": mat.get("outline_variant", "#7f849c"),
            "overlay0": mat.get("surface_variant", "#6c7086"),
            "surface2": mat.get("surface_container_high", "#585b70"),
            "surface1": mat.get("surface_container", "#45475a"),
            "surface0": mat.get("surface_container_low", "#313244"),
            "base": mat.get("surface", "#1e1e2e"),
            "mantle": mat.get("surface_dim", "#181825"),
            "crust": mat.get("surface_container_lowest", "#11111b"),
        }

    def _generate_static_palette(self, theme_data: dict) -> dict:
        """Generate palette from Catppuccin colors

        Extracts all 26 Catppuccin colors from theme data.

        Returns:
            Dict with 26 color keys mapping to hex values
        """
        ctp = get_catppuccin_colors(theme_data)

        return {
            "rosewater": ctp.get("rosewater", "#f5e0dc"),
            "flamingo": ctp.get("flamingo", "#f2cdcd"),
            "pink": ctp.get("pink", "#f5c2e7"),
            "mauve": ctp.get("mauve", "#cba6f7"),
            "red": ctp.get("red", "#f38ba8"),
            "maroon": ctp.get("maroon", "#eba0ac"),
            "peach": ctp.get("peach", "#fab387"),
            "yellow": ctp.get("yellow", "#f9e2af"),
            "green": ctp.get("green", "#a6e3a1"),
            "teal": ctp.get("teal", "#94e2d5"),
            "sky": ctp.get("sky", "#89dceb"),
            "sapphire": ctp.get("sapphire", "#74c7ec"),
            "blue": ctp.get("blue", "#89b4fa"),
            "lavender": ctp.get("lavender", "#b4befe"),
            "text": ctp.get("text", "#cdd6f4"),
            "subtext1": ctp.get("subtext1", "#bac2de"),
            "subtext0": ctp.get("subtext0", "#a6adc8"),
            "overlay2": ctp.get("overlay2", "#9399b2"),
            "overlay1": ctp.get("overlay1", "#7f849c"),
            "overlay0": ctp.get("overlay0", "#6c7086"),
            "surface2": ctp.get("surface2", "#585b70"),
            "surface1": ctp.get("surface1", "#45475a"),
            "surface0": ctp.get("surface0", "#313244"),
            "base": ctp.get("base", "#1e1e2e"),
            "mantle": ctp.get("mantle", "#181825"),
            "crust": ctp.get("crust", "#11111b"),
        }

    def _update_config(self, palette_name: str, palette_colors: dict) -> None:
        """Update starship.toml with new palette using tomlkit

        Clean approach: removes all existing palettes, adds only current one.
        Preserves all non-palette config (format, modules, comments).

        Args:
            palette_name: Name for the palette (e.g., "dynamic", "catppuccin_mocha")
            palette_colors: Dict of 26 color names to hex values
        """
        try:
            import tomlkit
        except ImportError:
            self.log_error("tomlkit not available - cannot update Starship config")
            self.log_warning("Install with: pip install tomlkit")
            return

        try:
            # Read existing config (preserves comments and structure)
            with open(self.config_file, "r") as f:
                config = tomlkit.load(f)

            # Update palette reference at root level
            config["palette"] = palette_name

            # Clean approach: remove ALL existing palettes
            if "palettes" in config:
                # Clear all palette entries
                config["palettes"].clear()
            else:
                # Create palettes section if it doesn't exist
                config["palettes"] = tomlkit.table()

            # Add the new palette
            config["palettes"][palette_name] = palette_colors

            # Write back (preserves comments and module configs)
            with open(self.config_file, "w") as f:
                tomlkit.dump(config, f)

            self.log_success(f'Updated Starship: palette = "{palette_name}"')

        except Exception as e:
            self.log_error(f"Failed to update Starship config: {e}")
