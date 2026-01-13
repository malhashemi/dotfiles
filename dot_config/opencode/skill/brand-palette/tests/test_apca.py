"""Tests for APCA contrast calculations."""

import pytest


class TestAPCACalculation:
    """Tests for APCA contrast calculation."""

    def test_black_on_white(self, apca_reference_pairs):
        from color_utils import calc_apca

        text, bg, expected, tolerance = apca_reference_pairs[0]
        lc = calc_apca(text, bg)
        assert abs(lc - expected) < tolerance

    def test_white_on_black(self, apca_reference_pairs):
        from color_utils import calc_apca

        text, bg, expected, tolerance = apca_reference_pairs[1]
        lc = calc_apca(text, bg)
        assert abs(lc - expected) < tolerance

    def test_gray_on_white(self, apca_reference_pairs):
        from color_utils import calc_apca

        text, bg, expected, tolerance = apca_reference_pairs[2]
        lc = calc_apca(text, bg)
        assert abs(lc - expected) < tolerance

    def test_polarity_matters(self):
        from color_utils import calc_apca

        # Black on white vs white on black should have opposite signs
        lc1 = calc_apca((0, 0, 0), (255, 255, 255))
        lc2 = calc_apca((255, 255, 255), (0, 0, 0))
        assert lc1 > 0  # Dark text on light bg is positive
        assert lc2 < 0  # Light text on dark bg is negative

    def test_same_color_zero_contrast(self):
        from color_utils import calc_apca

        lc = calc_apca((128, 128, 128), (128, 128, 128))
        assert abs(lc) < 1.0  # Near zero contrast


class TestAPCAFromRGB01:
    """Tests for RGB 0-1 wrapper."""

    def test_conversion_matches(self):
        from color_utils import calc_apca, calc_apca_from_rgb01

        lc1 = calc_apca((0, 0, 0), (255, 255, 255))
        lc2 = calc_apca_from_rgb01((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
        assert abs(lc1 - lc2) < 0.1


class TestAutoAdjustForContrast:
    """Tests for APCA auto-adjustment function."""

    def test_lighter_adjustment(self):
        from color_utils import auto_adjust_for_contrast

        # A color that needs to be lighter to achieve 60 Lc vs dark bg
        L_new, C_new, H, lc, success = auto_adjust_for_contrast(
            L=0.5,
            C=0.1,
            H=264.0,
            bg_rgb=(0.1, 0.1, 0.1),  # Dark background
            min_lc=60.0,
            direction="lighter",
            gamut="srgb",
            max_delta_l=0.3,
        )
        assert success
        assert L_new > 0.5  # Should be lighter
        assert lc >= 60.0  # Should meet threshold

    def test_darker_adjustment(self):
        from color_utils import auto_adjust_for_contrast

        # A color that needs to be darker to achieve 60 Lc vs light bg
        L_new, C_new, H, lc, success = auto_adjust_for_contrast(
            L=0.5,
            C=0.1,
            H=264.0,
            bg_rgb=(0.97, 0.97, 0.97),  # Light background
            min_lc=60.0,
            direction="darker",
            gamut="srgb",
            max_delta_l=0.3,
        )
        assert success
        assert L_new < 0.5  # Should be darker
        assert lc >= 60.0  # Should meet threshold

    def test_hue_preserved(self):
        from color_utils import auto_adjust_for_contrast

        original_H = 145.0
        L_new, C_new, H, lc, success = auto_adjust_for_contrast(
            L=0.7,
            C=0.1,
            H=original_H,
            bg_rgb=(0.1, 0.1, 0.1),
            min_lc=60.0,
            direction="lighter",
            gamut="srgb",
            max_delta_l=0.2,
        )
        # Hue should always be preserved
        assert H == original_H

    def test_max_delta_l_respected(self):
        from color_utils import auto_adjust_for_contrast

        max_delta = 0.1
        original_L = 0.5
        L_new, C_new, H, lc, success = auto_adjust_for_contrast(
            L=original_L,
            C=0.1,
            H=264.0,
            bg_rgb=(0.1, 0.1, 0.1),
            min_lc=60.0,
            direction="lighter",
            gamut="srgb",
            max_delta_l=max_delta,
        )
        # L change should not exceed max_delta_l
        assert abs(L_new - original_L) <= max_delta + 0.001


class TestP3APCA:
    """Tests for Display P3 APCA calculations."""

    def test_p3_coefficients_exist(self):
        from color_utils import _APCA_P3_RCO, _APCA_P3_GCO, _APCA_P3_BCO

        # P3 coefficients should be different from sRGB
        from color_utils import _APCA_S_RCO, _APCA_S_GCO, _APCA_S_BCO

        assert _APCA_P3_RCO != _APCA_S_RCO
        assert _APCA_P3_GCO != _APCA_S_GCO
        assert _APCA_P3_BCO != _APCA_S_BCO

        # P3 has slightly different coefficients due to wider primaries
        assert abs(_APCA_P3_RCO - 0.2289829594805780) < 1e-10
        assert abs(_APCA_P3_GCO - 0.6917492625852380) < 1e-10
        assert abs(_APCA_P3_BCO - 0.0792677779341829) < 1e-10

    def test_p3_to_y_apca(self):
        from color_utils import p3_to_y_apca

        # White should have Y close to 1
        y_white = p3_to_y_apca(1.0, 1.0, 1.0)
        assert abs(y_white - 1.0) < 0.01

        # Black should have Y close to 0
        y_black = p3_to_y_apca(0.0, 0.0, 0.0)
        assert y_black < 0.001

    def test_calc_apca_p3_black_on_white(self):
        from color_utils import calc_apca_p3

        # Black on white should give high positive contrast
        lc = calc_apca_p3((0.0, 0.0, 0.0), (1.0, 1.0, 1.0))
        assert lc > 100  # Should be around 106

    def test_calc_apca_p3_white_on_black(self):
        from color_utils import calc_apca_p3

        # White on black should give high negative contrast
        lc = calc_apca_p3((1.0, 1.0, 1.0), (0.0, 0.0, 0.0))
        assert lc < -100  # Should be around -108

    def test_p3_apca_differs_from_srgb_for_same_values(self):
        from color_utils import calc_apca_p3, calc_apca_from_rgb01

        # For the same numerical RGB values, P3 and sRGB APCA should differ
        # because they use different luminance coefficients
        text = (0.5, 0.3, 0.2)
        bg = (0.95, 0.95, 0.95)

        lc_p3 = calc_apca_p3(text, bg)
        lc_srgb = calc_apca_from_rgb01(text, bg)

        # They should be close but not identical
        assert lc_p3 != lc_srgb
        # The difference should be small (a few Lc points)
        assert abs(lc_p3 - lc_srgb) < 5

    def test_calc_apca_for_gamut_selects_correct_function(self):
        from color_utils import calc_apca_for_gamut, calc_apca_p3, calc_apca_from_rgb01

        text = (0.2, 0.4, 0.8)
        bg = (0.95, 0.95, 0.95)

        # P3 gamut should match calc_apca_p3
        lc_p3_via_gamut = calc_apca_for_gamut(text, bg, "p3")
        lc_p3_direct = calc_apca_p3(text, bg)
        assert lc_p3_via_gamut == lc_p3_direct

        # sRGB gamut should match calc_apca_from_rgb01
        lc_srgb_via_gamut = calc_apca_for_gamut(text, bg, "srgb")
        lc_srgb_direct = calc_apca_from_rgb01(text, bg)
        assert lc_srgb_via_gamut == lc_srgb_direct

    def test_auto_adjust_uses_p3_in_p3_mode(self):
        from color_utils import auto_adjust_for_contrast

        # Test that auto-adjust works in P3 mode
        L_new, C_new, H, lc, success = auto_adjust_for_contrast(
            L=0.5,
            C=0.1,
            H=264.0,
            bg_rgb=(0.1, 0.1, 0.1),  # P3 background
            min_lc=60.0,
            direction="lighter",
            gamut="p3",
            max_delta_l=0.3,
        )
        assert success
        assert L_new > 0.5
        assert lc >= 60.0
