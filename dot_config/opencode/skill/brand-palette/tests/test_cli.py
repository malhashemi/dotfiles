"""Tests for CLI argument parsing."""

import pytest
import subprocess
import sys
from pathlib import Path


# Get the scripts directory path
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
PALETTE_SCRIPT = SCRIPTS_DIR / "palette.py"


class TestHelpOutput:
    """Tests for --help output."""

    def test_help_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(PALETTE_SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_help_contains_sections(self):
        result = subprocess.run(
            [sys.executable, str(PALETTE_SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert "REQUIRED" in result.stdout
        assert "OUTPUT FORMAT" in result.stdout
        assert "VISUALIZATION" in result.stdout
        assert "COLOR OPTIONS" in result.stdout
        assert "ACCESSIBILITY" in result.stdout
        assert "EXAMPLES" in result.stdout

    def test_help_contains_new_flags(self):
        result = subprocess.run(
            [sys.executable, str(PALETTE_SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        # New flags from all phases
        assert "--auto-adjust" in result.stdout
        assert "--blocks" in result.stdout
        assert "--colored-text" in result.stdout
        assert "--gradient" in result.stdout
        assert "--format" in result.stdout
        assert "css" in result.stdout


class TestHueArgParsing:
    """Tests for --hue argument parsing."""

    def test_valid_single_hue(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--format",
                "json",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0

    def test_valid_multi_hue(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:0.6",
                "--hue",
                "Purple:0.4",
                "--format",
                "json",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0

    def test_invalid_hue_name(self):
        result = subprocess.run(
            [sys.executable, str(PALETTE_SCRIPT), "--hue", "NotAColor:1"],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode != 0
        assert "Unknown hue" in result.stderr or "error" in result.stderr.lower()

    def test_missing_weight(self):
        result = subprocess.run(
            [sys.executable, str(PALETTE_SCRIPT), "--hue", "Blue"],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode != 0


class TestFormatOptions:
    """Tests for --format options."""

    @pytest.mark.parametrize("fmt", ["palette", "tailwind", "json", "css", "css-hex"])
    def test_format_produces_output(self, fmt):
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--format",
                fmt,
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_format_none_produces_no_output(self):
        """Test that --format none produces no stdout output."""
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--format",
                "none",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_default_format_is_none(self):
        """Test that default format (no --format flag) produces no output."""
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_blocks_alone_no_format_output(self):
        """Test that --blocks without --format shows only visualization."""
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--blocks",
                "--no-color",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0
        # Should have block visualization
        assert "primary" in result.stdout
        # Should NOT have JSON output
        assert '"meta"' not in result.stdout
        # Should NOT have Tailwind output
        assert "module.exports" not in result.stdout

    def test_explicit_format_with_viz_works(self):
        """Test that --blocks with explicit --format shows both."""
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--blocks",
                "--format",
                "json",
                "--no-color",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0
        # Should have block visualization
        assert "primary" in result.stdout
        # Should have JSON output
        assert '"meta"' in result.stdout


class TestGamutOptions:
    """Tests for --gamut options."""

    @pytest.mark.parametrize("gamut", ["p3", "srgb"])
    def test_gamut_accepted(self, gamut):
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--gamut",
                gamut,
                "--format",
                "json",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0


class TestAutoAdjust:
    """Tests for --auto-adjust flag."""

    def test_auto_adjust_flag_accepted(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Yellow:1",
                "--auto-adjust",
                "--format",
                "palette",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0

    def test_auto_adjust_with_max_adjust(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Yellow:1",
                "--auto-adjust",
                "--max-adjust",
                "0.1",
                "--format",
                "palette",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0


class TestVisualizationFlags:
    """Tests for visualization flags."""

    def test_blocks_flag(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--blocks",
                "--no-color",
                "--format",
                "palette",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0
        assert "primary" in result.stdout  # Block visualization includes scale names

    def test_colored_text_flag(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--colored-text",
                "--no-color",
                "--format",
                "palette",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0
        assert "#" in result.stdout  # Hex values

    def test_gradient_flag(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--gradient",
                "--no-color",
                "--format",
                "palette",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0
        assert "deg" in result.stdout  # Gradient shows hue degrees

    def test_combined_visualization_flags(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PALETTE_SCRIPT),
                "--hue",
                "Blue:1",
                "--blocks",
                "--colored-text",
                "--no-color",
                "--format",
                "palette",
                "--quiet",
                "--no-validate-apca",
            ],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR),
        )
        assert result.returncode == 0
