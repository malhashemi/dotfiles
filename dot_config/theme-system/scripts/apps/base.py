"""Base class for theme-aware applications"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from rich.console import Console


class BaseApp(ABC):
    """Abstract base class for theme-aware applications

    Provides common functionality for all themed applications:
    - File writing with automatic directory creation
    - Command execution with error handling
    - Consistent logging messages

    Subclasses must implement:
    - apply_theme(theme_data: dict) -> None

    Subclasses may override:
    - requires_gui: bool = False  # Set True for GUI-only apps
    """

    # GUI requirement flag - override in subclasses for GUI-only apps
    # When True, app will be skipped on headless systems
    requires_gui: bool = False

    def __init__(self, name: str, config_home: Path):
        """Initialize base app

        Args:
            name: Human-readable app name (for logging)
            config_home: Path to ~/.config directory
        """
        self.name = name
        self.config_home = config_home
        self.console = Console()

    @abstractmethod
    def apply_theme(self, theme_data: dict) -> None:
        """Apply theme to application

        This method must be implemented by subclasses to generate
        configuration files and reload the application.

        Args:
            theme_data: Theme configuration dictionary containing:
                - theme.name: Theme name (dynamic, mocha, latte, etc.)
                - theme.variant: light/dark/amoled
                - theme.opacity: 0-100 opacity percentage
                - theme.colors: Catppuccin colors (static themes)
                - theme.material: Material Design 3 colors (all themes)
        """
        pass

    # File I/O utilities

    def write_file(self, path: Path, content: str, executable: bool = False) -> None:
        """Write file and optionally make it executable

        Args:
            path: File path to write
            content: File content
            executable: If True, chmod 755 the file
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

        if executable:
            path.chmod(0o755)

        self.log_success(f"Generated {path}")

    # Command execution utilities

    def run_command(
        self,
        command: list[str],
        error_msg: str | None = None,
        timeout: int = 5,
        silent_fail: bool = True,
    ) -> bool:
        """Run command with error handling

        Args:
            command: Command and arguments to execute
            error_msg: Custom error message to display on failure
            timeout: Command timeout in seconds
            silent_fail: If True, log warning on failure; if False, raise exception

        Returns:
            True if command succeeded, False otherwise

        Raises:
            RuntimeError: If command fails and silent_fail=False
        """
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=timeout)
            return True
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else str(e)
            msg = error_msg or f"Command failed: {' '.join(command)}"

            if silent_fail:
                self.log_warning(f"{msg}: {stderr}")
                return False
            else:
                raise RuntimeError(f"{msg}: {stderr}")

        except FileNotFoundError:
            msg = error_msg or f"Command not found: {command[0]}"

            if silent_fail:
                self.log_warning(msg)
                return False
            else:
                raise RuntimeError(msg)

        except subprocess.TimeoutExpired:
            msg = error_msg or f"Command timed out after {timeout}s"

            if silent_fail:
                self.log_warning(msg)
                return False
            else:
                raise RuntimeError(msg)

    def command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH

        Args:
            command: Command name to check

        Returns:
            True if command exists, False otherwise
        """
        try:
            result = subprocess.run(["which", command], capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False

    # Logging utilities

    def log_progress(self, message: str, emoji: str = "🎨") -> None:
        """Log progress message

        Args:
            message: Progress message
            emoji: Emoji to display before message
        """
        self.console.print(f"[blue]{emoji} {message}...[/blue]")

    def log_success(self, message: str) -> None:
        """Log success message

        Args:
            message: Success message
        """
        self.console.print(f"[green]✓ {message}[/green]")

    def log_warning(self, message: str) -> None:
        """Log warning message

        Args:
            message: Warning message
        """
        self.console.print(f"[yellow]⚠ {message}[/yellow]")

    def log_error(self, message: str) -> None:
        """Log error message

        Args:
            message: Error message
        """
        self.console.print(f"[red]✗ {message}[/red]")
