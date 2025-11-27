"""bottom theme generator"""

from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, get_catppuccin_colors, is_dynamic_theme


class BottomTheme(BaseApp):
    """bottom (btm) system monitor theme generator

    Updates the [styles] section in bottom.toml using surgical TOML editing.
    Preserves comments and user configuration while updating only theme colors.

    Method: Inline surgical swap (tomlkit)
    Reload: Manual - requires restart of btm (no hot-reload support)
    """

    def __init__(self, config_home: Path):
        super().__init__("bottom", config_home)
        self.config_file = config_home / "bottom/bottom.toml"

    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to bottom by updating [styles] sections"""

        # Check if config exists
        if not self.config_file.exists():
            self.log_warning(f"Config not found: {self.config_file}")
            self.log_warning("Skipping bottom theme update")
            return

        self.log_progress("Updating bottom theme")

        # Generate theme styles based on theme type
        if is_dynamic_theme(theme_data):
            styles = self._generate_dynamic_styles(theme_data)
        else:
            styles = self._generate_static_styles(theme_data)

        # Surgically update [styles] sections in config.toml
        self._update_styles_sections(styles)

        self.log_success(f"Updated {self.config_file}")
        self._log_reload_instructions()

    def _generate_dynamic_styles(self, theme_data: dict) -> dict:
        """Generate styles from Material Design 3 palette

        Maps MD3 semantic colors to bottom's style subsections.

        Returns:
            Dictionary of style sections with their color values
        """
        mat = get_material_colors(theme_data)

        return {
            "cpu": {
                "all_entry_color": mat.get("on_surface", "#cdd6f4"),
                "avg_entry_color": mat.get("error", "#f38ba8"),
                "cpu_core_colors": [
                    mat.get("primary", "#cba6f7"),
                    mat.get("secondary", "#f5c2e7"),
                    mat.get("tertiary", "#a6e3a1"),
                    mat.get("primary_container", "#89b4fa"),
                    mat.get("secondary_container", "#fab387"),
                    mat.get("tertiary_container", "#94e2d5"),
                ],
            },
            "memory": {
                "ram_color": mat.get("tertiary", "#a6e3a1"),
                "cache_color": mat.get("error", "#f38ba8"),
                "swap_color": mat.get("secondary", "#fab387"),
                "arc_color": mat.get("primary_container", "#89dceb"),
                "gpu_colors": [
                    mat.get("primary", "#89b4fa"),
                    mat.get("error", "#f38ba8"),
                    mat.get("tertiary", "#94e2d5"),
                    mat.get("tertiary_container", "#a6e3a1"),
                ],
            },
            "network": {
                "rx_color": mat.get("tertiary", "#a6e3a1"),
                "tx_color": mat.get("secondary", "#fab387"),
                "rx_total_color": mat.get("primary_container", "#94e2d5"),
                "tx_total_color": mat.get("primary", "#89b4fa"),
            },
            "battery": {
                "high_battery_color": mat.get("tertiary", "#a6e3a1"),
                "medium_battery_color": mat.get("secondary", "#f9e2af"),
                "low_battery_color": mat.get("error", "#f38ba8"),
            },
            "tables": {
                "headers": {"color": mat.get("primary", "#cba6f7"), "bold": True},
            },
            "graphs": {
                "graph_color": mat.get("outline", "#6c7086"),
                "legend_text": {"color": mat.get("on_surface_variant", "#a6adc8")},
            },
            "widgets": {
                "border_color": mat.get("outline", "#45475a"),
                "selected_border_color": mat.get("primary", "#cba6f7"),
                "widget_title": {"color": mat.get("on_surface", "#cdd6f4")},
                "text": {"color": mat.get("on_surface", "#cdd6f4")},
                "selected_text": {
                    "color": mat.get("on_primary", "#1e1e2e"),
                    "bg_color": mat.get("primary", "#cba6f7"),
                },
                "disabled_text": {"color": mat.get("outline_variant", "#7f849c")},
            },
        }

    def _generate_static_styles(self, theme_data: dict) -> dict:
        """Generate styles from Catppuccin palette

        Uses standard Catppuccin color mapping with mauve as primary accent.
        Based on official Catppuccin bottom theme structure.

        Returns:
            Dictionary of style sections with their color values
        """
        ctp = get_catppuccin_colors(theme_data)

        return {
            "cpu": {
                "all_entry_color": ctp.get("rosewater", "#f5e0dc"),
                "avg_entry_color": ctp.get("maroon", "#eba0ac"),
                "cpu_core_colors": [
                    ctp.get("mauve", "#cba6f7"),
                    ctp.get("blue", "#89b4fa"),
                    ctp.get("teal", "#94e2d5"),
                    ctp.get("green", "#a6e3a1"),
                    ctp.get("peach", "#fab387"),
                    ctp.get("red", "#f38ba8"),
                ],
            },
            "memory": {
                "ram_color": ctp.get("green", "#a6e3a1"),
                "cache_color": ctp.get("red", "#f38ba8"),
                "swap_color": ctp.get("peach", "#fab387"),
                "arc_color": ctp.get("sky", "#89dceb"),
                "gpu_colors": [
                    ctp.get("blue", "#89b4fa"),
                    ctp.get("red", "#f38ba8"),
                    ctp.get("teal", "#94e2d5"),
                    ctp.get("green", "#a6e3a1"),
                ],
            },
            "network": {
                "rx_color": ctp.get("green", "#a6e3a1"),
                "tx_color": ctp.get("peach", "#fab387"),
                "rx_total_color": ctp.get("teal", "#94e2d5"),
                "tx_total_color": ctp.get("blue", "#89b4fa"),
            },
            "battery": {
                "high_battery_color": ctp.get("green", "#a6e3a1"),
                "medium_battery_color": ctp.get("yellow", "#f9e2af"),
                "low_battery_color": ctp.get("red", "#f38ba8"),
            },
            "tables": {
                "headers": {"color": ctp.get("mauve", "#cba6f7"), "bold": True},
            },
            "graphs": {
                "graph_color": ctp.get("surface1", "#45475a"),
                "legend_text": {"color": ctp.get("subtext0", "#a6adc8")},
            },
            "widgets": {
                "border_color": ctp.get("surface0", "#313244"),
                "selected_border_color": ctp.get("mauve", "#cba6f7"),
                "widget_title": {"color": ctp.get("text", "#cdd6f4")},
                "text": {"color": ctp.get("text", "#cdd6f4")},
                "selected_text": {
                    "color": ctp.get("crust", "#11111b"),
                    "bg_color": ctp.get("mauve", "#cba6f7"),
                },
                "disabled_text": {"color": ctp.get("overlay0", "#6c7086")},
            },
        }

    def _update_styles_sections(self, styles: dict) -> None:
        """Surgically update [styles.*] sections in config.toml using tomlkit

        Preserves comments, formatting, and all other configuration sections.
        Only updates style color values in their respective subsections.

        Args:
            styles: Dictionary of style sections -> color values
        """
        try:
            import tomlkit
        except ImportError:
            self.log_error("tomlkit not available")
            self.log_warning("Install with: uv pip install tomlkit")
            return

        try:
            # Read existing config (preserves comments and formatting)
            with open(self.config_file, "r") as f:
                config = tomlkit.load(f)

            # Ensure [styles] section exists
            if "styles" not in config:
                config["styles"] = tomlkit.table()

            # Update each subsection (cpu, memory, network, etc.)
            for section_name, section_values in styles.items():
                if section_name not in config["styles"]:
                    config["styles"][section_name] = tomlkit.table()

                # Update values in this subsection
                for key, value in section_values.items():
                    config["styles"][section_name][key] = value

            # Write back (preserves structure)
            with open(self.config_file, "w") as f:
                tomlkit.dump(config, f)

        except Exception as e:
            self.log_error(f"Failed to update config: {e}")

    def _log_reload_instructions(self) -> None:
        """Show instructions for reloading bottom"""
        self.console.print(
            "[dim]  Note: Restart btm to apply changes (no hot-reload)[/dim]"
        )
