"""Ncspot theme generator"""

import os
import socket
import sys
from pathlib import Path
from .base import BaseApp
from utils import get_material_colors, get_catppuccin_colors, is_dynamic_theme


class NcspotTheme(BaseApp):
    """Ncspot (ncurses Spotify TUI) theme generator

    Updates the [theme] section in ncspot's config.toml using surgical TOML editing.
    Preserves comments and user configuration while updating only theme colors.

    Method: Inline surgical swap (tomlkit)
    Reload: Automatic via ncspot's IPC Unix socket — see ``_reload_app``.
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
        self._reload_app()
    
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
    
    # --- live reload -------------------------------------------------------

    def _reload_app(self) -> None:
        """Live-reload running ncspot(s) by sending ``reload`` over the IPC socket.

        ncspot opens a Unix-domain command socket (``ncspot.sock``) in its
        runtime directory and dispatches any line written to it through its
        command parser (upstream PR #1018, ncspot >= 0.10). The ``reload``
        command re-reads config.toml and re-applies the ``[theme]`` live via
        ``set_theme`` (upstream PR #243), so the freshly written colors appear
        without a restart or a manual ``:reload``.

        Unlike the opencode SIGUSR2 refresh, this emits NO OSC color queries to
        the host terminal — ncspot only repaints its own TUI — so it is safe to
        run while an opencode pane is mid-turn inside Herdr (no OSC-12 desync,
        ref herdr#806).

        The socket's presence is itself the capability probe: a build too old
        for command input (or simply not running) exposes no socket, so this is
        a quiet no-op and the colors are adopted on ncspot's next launch.
        """
        sockets = self._socket_paths()
        if not sockets:
            return  # not running / no socket — colors apply on next launch

        reloaded = sum(1 for sock_path in sockets if self._send_reload(sock_path))
        if reloaded:
            self.log_success(f"Reloaded {reloaded} ncspot instance(s) via IPC socket")

    def _socket_paths(self) -> list[Path]:
        """Return the IPC socket(s) for any running ncspot instance(s).

        The first instance owns ``ncspot.sock``; additional instances fall back
        to ``ncspot.<pid>.sock`` (upstream ipc.rs), so a glob picks up every
        live instance.
        """
        runtime_dir = self._runtime_dir()
        if runtime_dir is None or not runtime_dir.is_dir():
            return []
        return sorted(runtime_dir.glob("ncspot*.sock"))

    def _runtime_dir(self) -> Path | None:
        """Resolve ncspot's runtime directory, mirroring its own logic.

        Matches upstream ``utils::user_runtime_directory``: prefer
        ``$XDG_RUNTIME_DIR/ncspot``; on Linux fall back to
        ``/run/user/<uid>/ncspot``; otherwise (e.g. macOS) ``/tmp/ncspot-<uid>``.
        """
        xdg = os.environ.get("XDG_RUNTIME_DIR")
        if xdg:
            return Path(xdg) / "ncspot"

        uid = os.getuid()
        linux_runtime = Path(f"/run/user/{uid}")
        if sys.platform.startswith("linux") and linux_runtime.is_dir():
            return linux_runtime / "ncspot"

        tmp = Path("/tmp")
        if tmp.is_dir():
            return tmp / f"ncspot-{uid}"
        return None

    def _send_reload(self, sock_path: Path) -> bool:
        """Send a single ``reload`` command to one ncspot socket.

        ncspot's IPC handler multiplexes (``tokio::select!``) reading our command
        against writing player-status updates back to us, and it bails out of the
        whole handler on the first status-write error (the
        ``framed_writer.send(...)?`` in upstream ipc.rs). If we close immediately
        after writing, the status write ncspot emits on connect hits our closed
        socket, errors, and the handler returns *before* it reads our line — so
        ``reload`` is silently dropped. (This is why a live wallpaper change left
        ncspot un-themed until a manual ``:reload``.)

        To dodge the race: half-close our write side so ncspot still sees the line
        followed by EOF, keep our read side open, and drain ncspot's status output
        until it closes. With the read side open the status write always succeeds,
        so the handler stays alive long enough to read and execute ``reload``.

        Returns True once the command was written. A refused or timed-out
        connection means a stale socket from a dead instance — skipped quietly.
        """
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(2)
                sock.connect(str(sock_path))
                sock.sendall(b"reload\n")
                sock.shutdown(socket.SHUT_WR)
                # Read side stays open: drain status until ncspot closes (EOF) so
                # its writer never errors mid-select and drops the command first.
                while True:
                    try:
                        if not sock.recv(4096):
                            break
                    except socket.timeout:
                        break
            return True
        except OSError:
            return False
