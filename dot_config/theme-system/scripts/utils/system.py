"""System appearance and color extraction utilities"""

import json
import subprocess
import sys
from pathlib import Path


def detect_system_appearance() -> str:
    """Detect system appearance (light or dark)

    Platform support:
        - macOS: AppleScript / defaults
        - Linux: gsettings (GNOME/GTK)
        - Other: Falls back to 'dark'

    Returns:
        'light' or 'dark'
    """
    if sys.platform == "darwin":
        return _detect_macos_appearance()
    elif sys.platform == "linux":
        return _detect_linux_appearance()
    else:
        return "dark"


def _detect_macos_appearance() -> str:
    """Detect macOS system appearance"""
    try:
        # Use AppleScript to check dark mode setting
        result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to tell appearance preferences to get dark mode',
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )
        is_dark = result.stdout.strip().lower() == "true"
        return "dark" if is_dark else "light"
    except:
        # Fallback: check defaults (only exists in dark mode)
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return "dark" if "Dark" in result.stdout else "light"
        except:
            return "dark"


def _detect_linux_appearance() -> str:
    """Detect Linux system appearance via gsettings (GNOME/GTK)"""
    try:
        # Check GNOME/GTK color-scheme setting
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            output = result.stdout.strip().lower()
            if "dark" in output:
                return "dark"
            elif "light" in output:
                return "light"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Fallback: Check GTK theme name
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            theme = result.stdout.strip().lower()
            if "dark" in theme:
                return "dark"
            elif "light" in theme:
                return "light"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return "dark"


def set_system_appearance(appearance: str) -> bool:
    """Set system appearance

    Platform support:
        - macOS: AppleScript
        - Linux: gsettings (GNOME/GTK)
        - Other: No-op, returns False

    Args:
        appearance: 'light' or 'dark'

    Returns:
        True if successful, False otherwise
    """
    if sys.platform == "darwin":
        return _set_macos_appearance(appearance)
    elif sys.platform == "linux":
        return _set_linux_appearance(appearance)
    else:
        return False


def _set_macos_appearance(appearance: str) -> bool:
    """Set macOS system appearance"""
    try:
        dark_mode = "true" if appearance == "dark" else "false"
        subprocess.run(
            [
                "osascript",
                "-e",
                f'tell app "System Events" to tell appearance preferences to set dark mode to {dark_mode}',
            ],
            check=True,
            capture_output=True,
            timeout=5,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def _set_linux_appearance(appearance: str) -> bool:
    """Set Linux system appearance via gsettings (GNOME/GTK)

    Sets both color-scheme (GNOME 42+) and gtk-theme for broader compatibility.
    """
    success = False

    # Set GNOME color-scheme (GNOME 42+)
    try:
        color_scheme = "prefer-dark" if appearance == "dark" else "prefer-light"
        result = subprocess.run(
            [
                "gsettings",
                "set",
                "org.gnome.desktop.interface",
                "color-scheme",
                color_scheme,
            ],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            success = True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return success


def extract_colors_matugen(
    wallpaper_path: Path, mode: str = "dark", contrast: float = 0.0
) -> dict:
    """Extract colors using matugen with mode and contrast control

    Args:
        wallpaper_path: Path to wallpaper image
        mode: Color mode ('light', 'dark', or 'amoled')
        contrast: Contrast adjustment (-1.0 to 1.0, default 0)

    Returns:
        Dictionary of Material Design 3 colors

    Raises:
        RuntimeError: If matugen fails to extract colors
    """
    try:
        # Build matugen command
        cmd = ["matugen", "image", str(wallpaper_path), "-m", mode, "--json", "hex"]

        # Add contrast parameter if non-zero
        if contrast != 0.0:
            cmd.extend(["--contrast", str(contrast)])

        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)

        # Extract colors for the specified mode
        colors = data.get("colors", {}).get(mode, {})

        if not colors:
            raise RuntimeError(f"No colors generated for mode '{mode}'")

        return colors

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        raise RuntimeError(f"Matugen failed: {error_msg}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("Matugen timed out after 30 seconds")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse matugen output: {e}")
    except Exception as e:
        raise RuntimeError(f"Matugen failed: {e}")
