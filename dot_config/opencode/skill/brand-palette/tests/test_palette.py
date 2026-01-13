"""Tests for palette.py generation functions."""

import pytest
import json


class TestGenerateLightness:
    """Tests for lightness curve generation."""

    def test_t0_is_light(self):
        from palette import generate_lightness

        L = generate_lightness(0)
        assert 0.95 < L < 0.99  # Level 50 should be very light

    def test_t05_is_mid(self):
        from palette import generate_lightness

        L = generate_lightness(0.5)
        assert 0.55 < L < 0.65  # Level 500 should be mid (L_DARK=0.25)

    def test_t1_is_dark(self):
        from palette import generate_lightness

        L = generate_lightness(1.0)
        assert 0.20 < L < 0.30  # Level 950 retains visible hue (ColorBox style)

    def test_monotonic_decrease(self):
        from palette import generate_lightness

        prev = 1.0
        for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
            L = generate_lightness(t)
            assert L < prev
            prev = L


class TestChromaEnvelope:
    """Tests for chroma envelope function."""

    def test_minimum_at_edges(self):
        from palette import chroma_envelope

        # Edges now retain 15% of peak chroma for hue tinting
        assert chroma_envelope(0) == pytest.approx(0.15, abs=0.01)
        assert chroma_envelope(1) == pytest.approx(0.15, abs=0.01)

    def test_peak_at_middle(self):
        from palette import chroma_envelope

        assert chroma_envelope(0.5) == pytest.approx(1.0, abs=0.01)

    def test_symmetric(self):
        from palette import chroma_envelope

        assert chroma_envelope(0.25) == pytest.approx(chroma_envelope(0.75), abs=0.01)


class TestComputeScale:
    """Tests for scale generation."""

    def test_generates_11_levels(self):
        from palette import compute_scale, LEVELS

        scale = compute_scale("test", 264.0, 0.1, "srgb")
        assert len(scale.colors) == 11
        for level in LEVELS:
            assert level in scale.colors

    def test_neutral_low_chroma(self):
        from palette import compute_scale

        scale = compute_scale("neutral", 264.0, 0.0, "srgb", is_neutral=True)
        for color in scale.colors.values():
            # Max neutral chroma is now 0.10 (increased for visible tinting)
            assert color.oklch_c < 0.11


class TestGeneratePalette:
    """Tests for full palette generation."""

    def test_basic_generation(self):
        from palette import generate_palette

        palette = generate_palette(
            hue_weights=[("Blue", 1.0)],
            chroma_mode="even",
            gamut="srgb",
            palette_set="base",
        )
        assert "primary" in palette.scales
        assert "neutral" in palette.scales

    def test_full_set(self):
        from palette import generate_palette

        palette = generate_palette(
            hue_weights=[("Blue", 0.6), ("Purple", 0.4)],
            chroma_mode="even",
            gamut="p3",
            palette_set="full",
            include_complementary=True,
        )
        expected_scales = [
            "primary",
            "analogous-cool",
            "analogous-warm",
            "complement",
            "split-complement-cool",
            "split-complement-warm",
            "neutral",
        ]
        for name in expected_scales:
            assert name in palette.scales

    def test_apca_computed(self):
        from palette import generate_palette

        palette = generate_palette(
            hue_weights=[("Blue", 1.0)],
            chroma_mode="even",
            gamut="srgb",
            palette_set="base",
        )
        for scale in palette.scales.values():
            for color in scale.colors.values():
                assert color.apca_vs_light_bg is not None
                assert color.apca_vs_dark_bg is not None


class TestOutputFormats:
    """Tests for output format functions."""

    @pytest.fixture
    def sample_palette(self):
        from palette import generate_palette

        return generate_palette(
            hue_weights=[("Blue", 1.0)],
            chroma_mode="even",
            gamut="srgb",
            palette_set="base",
        )

    def test_palette_format(self, sample_palette):
        from palette import format_palette_block

        output = format_palette_block(sample_palette, "srgb")
        assert "```palette" in output
        assert "primary:" in output
        assert "neutral:" in output
        assert "```" in output

    def test_tailwind_format(self, sample_palette):
        from palette import format_tailwind_config

        output = format_tailwind_config(sample_palette)
        assert "module.exports" in output
        assert "theme:" in output
        assert "colors:" in output

    def test_json_format_valid(self, sample_palette):
        from palette import format_json

        output = format_json(sample_palette)
        data = json.loads(output)
        assert "meta" in data
        assert "scales" in data
        assert "primary" in data["scales"]

    def test_css_format(self, sample_palette):
        from palette import format_css

        output = format_css(sample_palette, use_oklch=True)
        assert ":root {" in output
        assert "--color-primary-" in output
        assert "oklch(" in output
        assert "}" in output

    def test_css_hex_format(self, sample_palette):
        from palette import format_css

        output = format_css(sample_palette, use_oklch=False)
        assert ":root {" in output
        assert "--color-primary-" in output
        assert "#" in output  # Hex values
        assert "oklch(" not in output


class TestFindAnchorLevel:
    """Tests for find_anchor_level function."""

    def test_mid_lightness(self):
        from palette import find_anchor_level

        level, t = find_anchor_level(0.55)
        assert level == 500  # L=0.55 is closest to level 500

    def test_light_lightness(self):
        from palette import find_anchor_level

        level, t = find_anchor_level(0.90)
        assert level in [100, 200]  # Light L matches light levels

    def test_dark_lightness(self):
        from palette import find_anchor_level

        level, t = find_anchor_level(0.25)
        assert level in [900, 950]  # L=0.25 is now darkest (L_DARK=0.25)


class TestGenerateLightnessAnchored:
    """Tests for anchored lightness generation."""

    def test_anchor_exact(self):
        from palette import generate_lightness_anchored

        L = generate_lightness_anchored(0.5, 0.60, 0.5)
        assert abs(L - 0.60) < 0.001  # Anchor is exact

    def test_endpoints_preserved(self):
        from palette import generate_lightness_anchored

        L_start = generate_lightness_anchored(0.0, 0.60, 0.5)
        L_end = generate_lightness_anchored(1.0, 0.60, 0.5)
        assert abs(L_start - 0.96) < 0.01  # Light end
        assert abs(L_end - 0.25) < 0.01  # Dark end (ColorBox style, retains hue)


class TestGenerateChromaAnchored:
    """Tests for anchored chroma generation."""

    def test_anchor_is_peak(self):
        from palette import generate_chroma_anchored

        C_anchor = generate_chroma_anchored(0.5, 0.19, 0.5)
        C_other = generate_chroma_anchored(0.3, 0.19, 0.5)
        assert abs(C_anchor - 0.19) < 0.001  # Anchor exact
        assert C_other < C_anchor  # Other levels lower


class TestComputeScaleAnchored:
    """Tests for anchored scale generation."""

    def test_anchor_level_exact(self):
        from palette import compute_scale_anchored

        scale = compute_scale_anchored(
            name="test",
            anchor_L=0.60,
            anchor_C=0.19,
            anchor_H=264.0,
            anchor_level=600,
            gamut="srgb",
        )
        color = scale.colors[600]
        assert abs(color.oklch_l - 0.60) < 0.001
        assert abs(color.oklch_c - 0.19) < 0.001
        assert abs(color.oklch_h - 264.0) < 0.1

    def test_generates_11_levels(self):
        from palette import compute_scale_anchored, LEVELS

        scale = compute_scale_anchored(
            name="test",
            anchor_L=0.55,
            anchor_C=0.15,
            anchor_H=200.0,
            anchor_level=500,
            gamut="p3",
        )
        assert len(scale.colors) == 11
        for level in LEVELS:
            assert level in scale.colors


class TestGenerateHueShifted:
    """Tests for ColorBox-style hue shifting."""

    def test_anchor_exact(self):
        from palette import generate_hue_shifted

        # At anchor, hue should be exact
        H = generate_hue_shifted(0.5, 260.0, 0.5, -16.0, 31.0)
        assert abs(H - 260.0) < 0.01

    def test_light_end_cooler(self):
        from palette import generate_hue_shifted

        # Light end should shift negative (toward cyan)
        H_light = generate_hue_shifted(0.0, 260.0, 0.5, -16.0, 31.0)
        assert H_light < 260.0  # Shifted negative (cooler)

    def test_dark_end_warmer(self):
        from palette import generate_hue_shifted

        # Dark end should shift positive (toward blue)
        H_dark = generate_hue_shifted(1.0, 260.0, 0.5, -16.0, 31.0)
        assert H_dark > 260.0  # Shifted positive (warmer)


class TestGenerateChromaColorbox:
    """Tests for ColorBox-style chroma generation."""

    def test_anchor_exact(self):
        from palette import generate_chroma_colorbox

        C = generate_chroma_colorbox(0.5, 0.15, 0.5, 0.55, 260.0, "p3")
        assert abs(C - 0.15) < 0.001

    def test_light_end_nonzero(self):
        from palette import generate_chroma_colorbox

        C = generate_chroma_colorbox(0.0, 0.15, 0.5, 0.97, 260.0, "p3")
        assert C > 0  # Should have some chroma, not zero

    def test_increases_up_to_anchor(self):
        from palette import generate_chroma_colorbox

        # Test that chroma increases from light end up to around anchor
        # (After anchor, gamut limits may cause decrease in dark levels)
        prev_C = 0
        for t in [0.0, 0.2, 0.4, 0.5]:  # Up to anchor at t=0.5
            L = 0.97 - 0.82 * t  # Approximate lightness
            C = generate_chroma_colorbox(t, 0.15, 0.5, L, 260.0, "p3")
            # Allow small tolerance for gamut clipping effects
            assert C >= prev_C - 0.01, (
                f"Chroma should increase up to anchor, but {C} < {prev_C}"
            )
            prev_C = C


class TestComputeScaleColorbox:
    """Tests for ColorBox-style scale generation."""

    def test_anchor_exact(self):
        from palette import compute_scale_colorbox

        scale = compute_scale_colorbox(
            name="test",
            anchor_L=0.55,
            anchor_C=0.15,
            anchor_H=260.0,
            anchor_level=500,
            gamut="p3",
        )
        color = scale.colors[500]
        assert abs(color.oklch_l - 0.55) < 0.001
        assert abs(color.oklch_c - 0.15) < 0.001
        assert abs(color.oklch_h - 260.0) < 0.1

    def test_hue_varies(self):
        from palette import compute_scale_colorbox

        scale = compute_scale_colorbox(
            name="test",
            anchor_L=0.55,
            anchor_C=0.15,
            anchor_H=260.0,
            anchor_level=500,
            gamut="p3",
            hue_shift=True,
        )
        H_50 = scale.colors[50].oklch_h
        H_950 = scale.colors[950].oklch_h
        assert H_50 != H_950  # Hue should vary

    def test_generates_11_levels(self):
        from palette import compute_scale_colorbox, LEVELS

        scale = compute_scale_colorbox(
            name="test",
            anchor_L=0.55,
            anchor_C=0.15,
            anchor_H=260.0,
            anchor_level=500,
            gamut="p3",
        )
        assert len(scale.colors) == 11
        for level in LEVELS:
            assert level in scale.colors
