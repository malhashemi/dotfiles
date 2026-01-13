"""Shared pytest fixtures for brand-palette skill tests."""

import pytest
import re
import sys
from pathlib import Path

# Add scripts directory to path (sibling to tests/)
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# ANSI escape code pattern
ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


@pytest.fixture
def strip_ansi():
    """Fixture to strip ANSI escape codes from text."""

    def _strip(text: str) -> str:
        return ANSI_ESCAPE.sub("", text)

    return _strip


@pytest.fixture
def color_tolerance():
    """Tolerance values for color comparisons."""
    return {
        "L": 0.001,
        "C": 0.001,
        "H": 0.5,
        "rgb": 1,  # 0-255 range
        "apca": 0.5,  # Lc tolerance
    }


@pytest.fixture
def reference_colors():
    """Reference colors for testing conversions."""
    return {
        "white": {
            "hex": "#FFFFFF",
            "rgb01": (1.0, 1.0, 1.0),
            "rgb255": (255, 255, 255),
            "oklch_L": 1.0,
            "oklch_C": 0.0,
        },
        "black": {
            "hex": "#000000",
            "rgb01": (0.0, 0.0, 0.0),
            "rgb255": (0, 0, 0),
            "oklch_L": 0.0,
            "oklch_C": 0.0,
        },
        "red": {
            "hex": "#FF0000",
            "rgb01": (1.0, 0.0, 0.0),
            "rgb255": (255, 0, 0),
            "oklch_L": 0.628,
            "oklch_C": 0.258,
            "oklch_H": 29.2,
        },
        "gray": {
            "hex": "#808080",
            "rgb01": (0.502, 0.502, 0.502),
            "rgb255": (128, 128, 128),
        },
    }


@pytest.fixture
def apca_reference_pairs():
    """Reference text/bg pairs with known APCA Lc values."""
    return [
        # (text_rgb_255, bg_rgb_255, expected_Lc, tolerance)
        ((0, 0, 0), (255, 255, 255), 106.0, 1.0),  # Black on white
        ((255, 255, 255), (0, 0, 0), -108.0, 1.0),  # White on black
        ((128, 128, 128), (255, 255, 255), 67.0, 2.0),  # Gray on white
        ((0, 0, 0), (128, 128, 128), 58.0, 2.0),  # Black on gray
    ]


@pytest.fixture
def scripts_dir():
    """Path to the scripts directory."""
    return Path(__file__).parent.parent / "scripts"
