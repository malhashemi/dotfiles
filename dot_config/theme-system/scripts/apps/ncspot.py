"""Ncspot theme generator"""

from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, get_catppuccin_colors, is_dynamic_theme


class NcspotTheme(BaseApp):
    """Ncspot (ncurses Spotify TUI) theme generator
    
    Updates the [theme] section in ncspot's config.toml using surgical TOML editing.
    Preserves comments and user configuration while updating only theme colors.
    
    Method: Inline surgical swap (tomlkit)
    Reload: Manual via :reload command in ncspot
    """
    
    def __init__(self, config_home: Path):
        super().__init__("ncspot", config_home)
        self.config_file = config_home / "ncspot/config.toml"
    
    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to ncspot by updating [theme] section"""
        
        # Check if config exists
        if not self.config_file.exists():
            self.log_warning(f"Config not found: {self.config_file}")
            self.log_warning("Skipping ncspot theme update")
            return
        
        self.log_progress("Updating ncspot theme")
        
        # Generate theme colors based on theme type
        if is_dynamic_theme(theme_data):
            theme_colors = self._generate_dynamic_colors(theme_data)
        else:
            theme_colors = self._generate_static_colors(theme_data)
        
        # Surgically update [theme] section in config.toml
        self._update_theme_section(theme_colors)
        
        self.log_success(f"Updated {self.config_file}")
        self._log_reload_instructions()
    
    def _generate_dynamic_colors(self, theme_data: dict) -> dict:
        """Generate theme colors from Material Design 3 palette
        
        Uses empty strings for backgrounds to achieve complete transparency.
        
        Returns:
            Dictionary of ncspot theme keys -> color values (hex or empty string)
        """
        mat = get_material_colors(theme_data)
        
        return {
            'background': '',                   # Empty: no background, fully transparent
            'primary': mat.get('on_surface', '#cdd6f4'),
            'secondary': mat.get('on_surface_variant', '#94e2d5'),
            'title': mat.get('primary', '#cba6f7'),
            'playing': mat.get('tertiary', '#a6e3a1'),
            'playing_bg': '',                   # Empty: no background, fully transparent
            'highlight': mat.get('on_primary_container', '#cdd6f4'),
            'highlight_bg': mat.get('primary_container', '#585b70'),
            'playing_selected': mat.get('tertiary', '#a6e3a1'),
            'error': mat.get('on_error', '#1e1e2e'),
            'error_bg': mat.get('error', '#f38ba8'),
            'statusbar': mat.get('primary', '#cba6f7'),
            'statusbar_bg': '',                 # Empty: no background, fully transparent
            'statusbar_progress': mat.get('primary', '#cba6f7'),
            'cmdline': mat.get('primary', '#cba6f7'),
            'cmdline_bg': '',                   # Empty: no background, fully transparent
            'search_match': mat.get('error', '#f38ba8'),
        }
    
    def _generate_static_colors(self, theme_data: dict) -> dict:
        """Generate theme colors from Catppuccin palette
        
        Uses empty strings for backgrounds to achieve complete transparency.
        Based on official Catppuccin ncspot theme mappings.
        
        Returns:
            Dictionary of ncspot theme keys -> color values (hex or empty string)
        """
        ctp = get_catppuccin_colors(theme_data)
        
        # Based on official Catppuccin ncspot themes
        # https://github.com/catppuccin/ncspot
        return {
            'background': '',                   # Empty: no background, fully transparent
            'primary': ctp.get('text', '#cdd6f4'),
            'secondary': ctp.get('teal', '#94e2d5'),
            'title': ctp.get('mauve', '#cba6f7'),
            'playing': ctp.get('green', '#a6e3a1'),
            'playing_bg': '',                   # Empty: no background, fully transparent
            'highlight': ctp.get('text', '#cdd6f4'),
            'highlight_bg': ctp.get('surface2', '#585b70'),
            'playing_selected': ctp.get('green', '#a6e3a1'),
            'error': ctp.get('base', '#1e1e2e'),
            'error_bg': ctp.get('red', '#f38ba8'),
            'statusbar': ctp.get('mauve', '#cba6f7'),
            'statusbar_bg': '',                 # Empty: no background, fully transparent
            'statusbar_progress': ctp.get('mauve', '#cba6f7'),
            'cmdline': ctp.get('mauve', '#cba6f7'),
            'cmdline_bg': '',                   # Empty: no background, fully transparent
            'search_match': ctp.get('red', '#f38ba8'),
        }
    
    def _update_theme_section(self, theme_colors: dict) -> None:
        """Surgically update [theme] section in config.toml using tomlkit
        
        Preserves comments, formatting, and all other configuration sections.
        Only updates theme color values.
        
        Args:
            theme_colors: Dictionary of theme keys -> color values (hex or empty string)
        """
        try:
            import tomlkit
        except ImportError:
            self.log_error("tomlkit not available")
            self.log_warning("Install with: uv pip install tomlkit")
            return
        
        try:
            # Read existing config (preserves comments and formatting)
            with open(self.config_file, 'r') as f:
                config = tomlkit.load(f)
            
            # Ensure [theme] section exists
            if 'theme' not in config:
                config['theme'] = {}
            
            # Surgically update only theme values
            config['theme'].update(theme_colors)
            
            # Write back (preserves structure)
            with open(self.config_file, 'w') as f:
                tomlkit.dump(config, f)
                
        except tomlkit.exceptions.TOMLKitError as e:
            self.log_error(f"Failed to parse TOML: {e}")
            self.log_warning("Fix syntax errors in config.toml and try again")
        except Exception as e:
            self.log_error(f"Failed to update config: {e}")
    
    def _log_reload_instructions(self) -> None:
        """Show instructions for reloading ncspot"""
        self.console.print(
            "[dim]  Reload: Open ncspot and type :reload[/dim]"
        )
