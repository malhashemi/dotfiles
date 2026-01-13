"""Tests for terminal visualization functions."""

import pytest


class TestTerminalUtilities:
    """Tests for ANSI escape code utilities."""

    def test_rgb_fg(self):
        from palette import rgb_fg, RESET

        code = rgb_fg(255, 0, 0)
        assert "\x1b[38;2;255;0;0m" in code

    def test_rgb_bg(self):
        from palette import rgb_bg

        code = rgb_bg(0, 255, 0)
        assert "\x1b[48;2;0;255;0m" in code

    def test_reset_code(self):
        from palette import RESET

        assert RESET == "\x1b[0m"

    def test_rgb01_to_255(self):
        from palette import rgb01_to_255

        r, g, b = rgb01_to_255(1.0, 0.5, 0.0)
        assert r == 255
        assert g == 128
        assert b == 0


class TestFormatBlocks:
    """Tests for block visualization."""

    @pytest.fixture
    def sample_palette(self):
        from palette import generate_palette

        return generate_palette(
            hue_weights=[("Blue", 1.0)],
            chroma_mode="even",
            gamut="srgb",
            palette_set="base",
        )

    def test_has_scale_names(self, sample_palette):
        from palette import format_blocks

        output = format_blocks(sample_palette, "srgb", use_color=False)
        assert "primary" in output
        assert "neutral" in output

    def test_has_level_labels(self, sample_palette):
        from palette import format_blocks

        output = format_blocks(sample_palette, "srgb", use_color=False)
        assert "50" in output
        assert "500" in output
        assert "950" in output

    def test_no_ansi_when_disabled(self, sample_palette, strip_ansi):
        from palette import format_blocks

        output = format_blocks(sample_palette, "srgb", use_color=False)
        assert output == strip_ansi(output)

    def test_has_ansi_when_enabled(self, sample_palette, strip_ansi):
        from palette import format_blocks

        output = format_blocks(sample_palette, "srgb", use_color=True)
        assert output != strip_ansi(output)


class TestFormatColoredText:
    """Tests for colored text visualization."""

    @pytest.fixture
    def sample_palette(self):
        from palette import generate_palette

        return generate_palette(
            hue_weights=[("Blue", 1.0)],
            chroma_mode="even",
            gamut="srgb",
            palette_set="base",
        )

    def test_contains_hex_values(self, sample_palette):
        from palette import format_colored_text

        output = format_colored_text(sample_palette, "srgb", use_color=False)
        assert "#" in output  # Hex values present

    def test_no_ansi_when_disabled(self, sample_palette, strip_ansi):
        from palette import format_colored_text

        output = format_colored_text(sample_palette, "srgb", use_color=False)
        assert output == strip_ansi(output)


class TestFormatGradient:
    """Tests for gradient visualization."""

    @pytest.fixture
    def sample_palette(self):
        from palette import generate_palette

        return generate_palette(
            hue_weights=[("Blue", 1.0)],
            chroma_mode="even",
            gamut="srgb",
            palette_set="base",
        )

    def test_contains_scale_info(self, sample_palette):
        from palette import format_gradient

        output = format_gradient(sample_palette, "srgb", use_color=False)
        assert "primary" in output
        assert "deg" in output  # Hue angle

    def test_has_gradient_chars(self, sample_palette):
        from palette import format_gradient, LIGHT_SHADE, DARK_SHADE, FULL_BLOCK

        output = format_gradient(sample_palette, "srgb", use_color=False)
        # Should contain at least one gradient character
        has_gradient = any(c in output for c in [LIGHT_SHADE, DARK_SHADE, FULL_BLOCK])
        assert has_gradient
