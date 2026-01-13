"""Tests for color_utils.py core functions."""

import pytest
import math


class TestClamp:
    """Tests for clamp function."""

    def test_value_in_range(self):
        from color_utils import clamp

        assert clamp(0.5, 0.0, 1.0) == 0.5

    def test_value_below_range(self):
        from color_utils import clamp

        assert clamp(-0.5, 0.0, 1.0) == 0.0

    def test_value_above_range(self):
        from color_utils import clamp

        assert clamp(1.5, 0.0, 1.0) == 1.0

    def test_value_at_bounds(self):
        from color_utils import clamp

        assert clamp(0.0, 0.0, 1.0) == 0.0
        assert clamp(1.0, 0.0, 1.0) == 1.0


class TestMod360:
    """Tests for mod360 function."""

    def test_positive_in_range(self):
        from color_utils import mod360

        assert mod360(180.0) == 180.0

    def test_negative(self):
        from color_utils import mod360

        assert mod360(-90.0) == 270.0

    def test_over_360(self):
        from color_utils import mod360

        assert mod360(450.0) == 90.0


class TestRybHsvHueConversion:
    """Tests for 48-point RYB <-> HSV hue conversion."""

    def test_red_unchanged(self):
        """Red should map to itself in both directions."""
        from color_utils import ryb_hue_to_hsv_hue, hsv_hue_to_ryb_hue

        # RYB Red (0°) -> HSV Red (0°)
        assert abs(ryb_hue_to_hsv_hue(0.0) - 0.0) < 0.1
        # HSV Red (0°) -> RYB Red (0°)
        assert abs(hsv_hue_to_ryb_hue(0.0) - 0.0) < 0.1

    def test_hsv_yellow_to_ryb(self):
        """HSV Yellow (60°) should map to RYB ~34° (orange-yellow region)."""
        from color_utils import hsv_hue_to_ryb_hue

        # HSV 53° (Yellow) -> RYB 120° (tuned Paletton mapping)
        # Note: We tuned (120, 53) so HSV 53° maps to RYB 120°
        result = hsv_hue_to_ryb_hue(53.0)
        assert abs(result - 120.0) < 0.1

    def test_hsv_blue_to_ryb(self):
        """HSV Blue (240°) should map to RYB ~275° (Kuler/Paletton mapping)."""
        from color_utils import hsv_hue_to_ryb_hue

        # HSV 240° (Blue) -> RYB 275° (Kuler/Paletton mapping)
        result = hsv_hue_to_ryb_hue(240.0)
        assert abs(result - 275.0) < 0.1

    def test_blue_complement_is_orange(self):
        """Key test: Blue's RYB complement should be in the orange region."""
        from color_utils import hsv_hue_to_ryb_hue, ryb_hue_to_hsv_hue

        # 1. Convert HSV Blue to RYB
        blue_hsv = 240.0
        blue_ryb = hsv_hue_to_ryb_hue(blue_hsv)
        assert abs(blue_ryb - 275.0) < 1.0  # RYB ~275° (Kuler/Paletton)

        # 2. Calculate complement in RYB space
        complement_ryb = (blue_ryb + 180.0) % 360.0  # Should be ~95°

        # 3. Convert complement back to HSV
        complement_hsv = ryb_hue_to_hsv_hue(complement_ryb)

        # 4. Complement should be in orange/yellow range (HSV 35-60°)
        assert 35.0 < complement_hsv < 65.0, (
            f"Expected orange/yellow (35-65°), got {complement_hsv}°"
        )

    def test_roundtrip_consistency(self):
        """Converting HSV -> RYB -> HSV should return close to original."""
        from color_utils import ryb_hue_to_hsv_hue, hsv_hue_to_ryb_hue

        # Test several hue values
        for hsv_hue in [0, 30, 60, 90, 120, 180, 240, 300]:
            ryb_hue = hsv_hue_to_ryb_hue(float(hsv_hue))
            back_to_hsv = ryb_hue_to_hsv_hue(ryb_hue)
            assert abs(back_to_hsv - hsv_hue) < 1.0, (
                f"Roundtrip failed for HSV {hsv_hue}°"
            )

    def test_backward_compatible_aliases(self):
        """The old function names should still work as aliases."""
        from color_utils import (
            ryb_hue_to_rgb_hue,
            rgb_hue_to_ryb_hue,
            ryb_hue_to_hsv_hue,
            hsv_hue_to_ryb_hue,
        )

        # Aliases should produce identical results
        assert ryb_hue_to_rgb_hue(45.0) == ryb_hue_to_hsv_hue(45.0)
        assert rgb_hue_to_ryb_hue(120.0) == hsv_hue_to_ryb_hue(120.0)


class TestOklchConversions:
    """Tests for OKLCH color conversions."""

    def test_white_roundtrip(self, reference_colors):
        from color_utils import oklch_to_srgb

        white = reference_colors["white"]
        r, g, b, in_gamut = oklch_to_srgb(white["oklch_L"], white["oklch_C"], 0)
        assert in_gamut
        assert abs(r - 1.0) < 0.01
        assert abs(g - 1.0) < 0.01
        assert abs(b - 1.0) < 0.01

    def test_black_roundtrip(self, reference_colors):
        from color_utils import oklch_to_srgb

        black = reference_colors["black"]
        r, g, b, in_gamut = oklch_to_srgb(black["oklch_L"], black["oklch_C"], 0)
        assert in_gamut
        assert abs(r) < 0.01
        assert abs(g) < 0.01
        assert abs(b) < 0.01

    def test_out_of_gamut_detection(self):
        from color_utils import oklch_to_srgb

        # High chroma at mid lightness should be out of sRGB gamut
        _, _, _, in_gamut = oklch_to_srgb(0.5, 0.4, 145)
        assert not in_gamut


class TestCmaxForLH:
    """Tests for maximum chroma search."""

    def test_zero_lightness(self):
        from color_utils import cmax_for_L_h

        # At L=0 (black), max chroma should be near 0
        cmax = cmax_for_L_h(0.0, 0, "srgb")
        assert cmax < 0.01

    def test_full_lightness(self):
        from color_utils import cmax_for_L_h

        # At L=1 (white), max chroma should be near 0
        cmax = cmax_for_L_h(1.0, 0, "srgb")
        assert cmax < 0.01

    def test_p3_larger_than_srgb(self):
        from color_utils import cmax_for_L_h

        # P3 should allow higher chroma than sRGB for most hues
        cmax_srgb = cmax_for_L_h(0.6, 145, "srgb")
        cmax_p3 = cmax_for_L_h(0.6, 145, "p3")
        assert cmax_p3 > cmax_srgb


class TestHexToOklch:
    """Tests for hex to OKLCH conversion."""

    def test_known_color(self):
        from color_utils import hex_to_oklch

        # User's reference teal color
        L, C, H = hex_to_oklch("#015856")
        assert abs(L - 0.416) < 0.01
        assert abs(C - 0.071) < 0.01
        assert abs(H - 192.0) < 1.0

    def test_pure_blue(self):
        from color_utils import hex_to_oklch

        L, C, H = hex_to_oklch("#0000FF")
        # Blue should be around hue 264
        assert 260 < H < 270
        assert C > 0.2  # High chroma

    def test_white(self):
        from color_utils import hex_to_oklch

        L, C, H = hex_to_oklch("#FFFFFF")
        assert abs(L - 1.0) < 0.01
        assert C < 0.01  # No chroma

    def test_black(self):
        from color_utils import hex_to_oklch

        L, C, H = hex_to_oklch("#000000")
        assert L < 0.01
        assert C < 0.01

    def test_without_hash(self):
        from color_utils import hex_to_oklch

        # Should work with or without #
        L1, C1, H1 = hex_to_oklch("#FF5500")
        L2, C2, H2 = hex_to_oklch("FF5500")
        assert abs(L1 - L2) < 0.001
        assert abs(C1 - C2) < 0.001
        assert abs(H1 - H2) < 0.1


class TestSrgbToOklch:
    """Tests for sRGB to OKLCH conversion."""

    def test_roundtrip(self):
        from color_utils import srgb_to_oklch, oklch_to_srgb

        # Convert sRGB -> OKLCH -> sRGB
        L, C, H = srgb_to_oklch(0.5, 0.3, 0.8)
        r, g, b, _ = oklch_to_srgb(L, C, H)
        assert abs(r - 0.5) < 0.01
        assert abs(g - 0.3) < 0.01
        assert abs(b - 0.8) < 0.01

    def test_gray(self):
        from color_utils import srgb_to_oklch

        # Gray should have near-zero chroma
        L, C, H = srgb_to_oklch(0.5, 0.5, 0.5)
        assert C < 0.01
