#!/usr/bin/env python3
"""
scripts/palette.py

Generate full 11-step tonal palettes from RYB hue mixes using OKLCH.

Features:
- 11-step scales (50-950) for each harmonic hue
- Tinted neutrals with primary hue
- Even/Max chroma modes
- P3 gamut support (default) with sRGB fallback
- APCA contrast validation
- Multiple output formats (palette, tailwind, json)

Examples:
    uv run scripts/palette.py \\
        --hue Blue:0.55 --hue Purple:0.30 --hue Green:0.15 \\
        --chroma-mode even --format palette

    uv run scripts/palette.py \\
        --hue Blue:1 --gamut srgb --format all
"""

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Tuple

if TYPE_CHECKING:
    from brandcolor import BrandColorResult

from color_utils import (
    # Basic utilities
    clamp,
    mod360,
    circular_mean_deg,
    # RYB/RGB/OKLCH conversion
    ryb_hue_to_rgb_hue,
    rgb_hue_to_oklch_hue_deg,
    # Color conversions
    oklch_to_srgb,
    oklch_to_p3,
    hex_from_rgb01,
    css_p3_string,
    p3_to_srgb_fallback,
    oklch_in_p3_gamut,
    linear_rgb_in_gamut,
    oklch_to_linear_srgb,
    # HSB/HSV conversions (for ColorBox algorithm)
    hsv_to_srgb,
    srgb_to_hsv,
    srgb_to_oklch,
    # Max chroma
    cmax_for_L_h,
    # APCA
    calc_apca_from_rgb01,
    calc_apca_p3,
    APCA_THRESHOLD_LARGE_TEXT,
    # Shared hue parsing utilities
    RYB_ANCHOR_DEG,
    normalize_hue_name,
    parse_hue_arg,
)

# ========== Type Definitions ==========

Gamut = Literal["srgb", "p3"]
ChromaMode = Literal["even", "max", "both", "anchored"]
OutputFormat = Literal["palette", "tailwind", "json", "css", "css-hex", "all", "none"]

# ========== Terminal Utilities ==========

ESC = "\x1b"
RESET = f"{ESC}[0m"

# Unicode block characters
FULL_BLOCK = "\u2588"  # █
DARK_SHADE = "\u2593"  # ▓
MEDIUM_SHADE = "\u2592"  # ▒
LIGHT_SHADE = "\u2591"  # ░


def rgb_fg(r: int, g: int, b: int) -> str:
    """ANSI foreground color escape sequence."""
    return f"{ESC}[38;2;{r};{g};{b}m"


def rgb_bg(r: int, g: int, b: int) -> str:
    """ANSI background color escape sequence."""
    return f"{ESC}[48;2;{r};{g};{b}m"


def supports_truecolor() -> bool:
    """Check if terminal supports 24-bit color."""
    colorterm = os.environ.get("COLORTERM", "").lower()
    return colorterm in ("truecolor", "24bit")


def should_use_color(force: bool = False, no_color: bool = False) -> bool:
    """Determine if ANSI colors should be used."""
    if no_color or os.environ.get("NO_COLOR"):
        return False
    if force or os.environ.get("FORCE_COLOR"):
        return True
    return sys.stdout.isatty() and supports_truecolor()


def rgb01_to_255(r: float, g: float, b: float) -> Tuple[int, int, int]:
    """Convert RGB 0-1 to 0-255."""
    return (
        int(round(clamp(r, 0.0, 1.0) * 255)),
        int(round(clamp(g, 0.0, 1.0) * 255)),
        int(round(clamp(b, 0.0, 1.0) * 255)),
    )


# ========== Constants ==========

# Tonal scale levels (Tailwind convention)
LEVELS = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]

# Level to t (0-1) mapping
LEVEL_TO_T = {level: i / (len(LEVELS) - 1) for i, level in enumerate(LEVELS)}


# ========== Easing Functions ==========


def ease_in_quad(t: float) -> float:
    """Quadratic ease-in: slow start, fast finish."""
    return t * t


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out: fast start, slow finish."""
    return t * (2 - t)


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out: slow at both ends."""
    return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t


# ========== ColorBox Algorithm for Neutrals ==========
#
# ColorBox (https://github.com/Automattic/colorbox) generates palettes
# by interpolating Hue, Saturation, and Brightness independently with
# different easing curves.
#
# For neutrals derived from a brand color:
#   - HUE: Rotates ±15° around the base hue (easeOut, clockwise)
#   - SATURATION: 0 → 0.9 (easeIn) - clean whites, tinted darks
#   - BRIGHTNESS: 0.99 → 0.1 (easeInOut) - smooth light-to-dark


def colorbox_interpolate_hue(
    start_hue: float,
    end_hue: float,
    t: float,
    clockwise: bool = True,
) -> float:
    """
    Interpolate hue with rotation direction.

    Args:
        start_hue: Starting hue (degrees)
        end_hue: Ending hue (degrees)
        t: Progress (0-1), already eased
        clockwise: If True, go clockwise (increasing hue)

    Returns:
        Interpolated hue (0-360)
    """
    if clockwise:
        # Clockwise: if end < start, wrap around 360
        if end_hue >= start_hue:
            hue_delta = end_hue - start_hue
        else:
            hue_delta = (360 - start_hue) + end_hue
    else:
        # Counter-clockwise: if start < end, wrap around negative
        if start_hue >= end_hue:
            hue_delta = -(start_hue - end_hue)
        else:
            hue_delta = -(start_hue + (360 - end_hue))

    hue = start_hue + hue_delta * t
    return mod360(hue)


def compute_neutral_scale_colorbox(
    base_hsb_hue: float,
    gamut: Gamut,
    hue_shift: float = 15.0,
    sat_start: float = 0.0,
    sat_end: float = 0.9,
    bri_start: float = 0.99,
    bri_end: float = 0.10,
) -> "ColorScale":
    """
    Generate neutral scale using ColorBox algorithm.

    This creates neutrals that:
    - Have clean whites (low saturation at light end)
    - Progressively tint toward the brand hue in darks
    - Subtly shift hue across the scale for visual richness

    ColorBox Settings (as specified):
        HUE:        Start=baseHue-15, End=baseHue+15, Clockwise, easeOut
        SATURATION: Start=0, End=0.9, easeIn
        BRIGHTNESS: Start=0.99, End=0.1, easeInOut

    Args:
        base_hsb_hue: The primary brand color's HSB hue (0-360)
        gamut: Target gamut ("p3" or "srgb")
        hue_shift: Degrees to shift hue ± from base (default 15)
        sat_start: Starting saturation (default 0)
        sat_end: Ending saturation (default 0.9)
        bri_start: Starting brightness (default 0.99)
        bri_end: Ending brightness (default 0.10)

    Returns:
        ColorScale with 11 levels (50-950) in OKLCH
    """
    # Hue range
    hue_start = mod360(base_hsb_hue - hue_shift)
    hue_end = mod360(base_hsb_hue + hue_shift)

    # We'll store the mid-point hue as the scale's oklch_hue for reference
    scale = ColorScale(name="neutral", oklch_hue=rgb_hue_to_oklch_hue_deg(base_hsb_hue))

    for level in LEVELS:
        t = LEVEL_TO_T[level]

        # Apply ColorBox curves:
        # HUE: easeOut (fast start, slow finish)
        hue_t = ease_out_quad(t)
        hsb_hue = colorbox_interpolate_hue(hue_start, hue_end, hue_t, clockwise=True)

        # SATURATION: easeIn (slow start, fast finish)
        sat_t = ease_in_quad(t)
        hsb_sat = sat_start + (sat_end - sat_start) * sat_t

        # BRIGHTNESS: easeInOut (slow at both ends)
        bri_t = ease_in_out_quad(t)
        hsb_bri = bri_start + (bri_end - bri_start) * bri_t

        # Convert HSB to sRGB (0-1)
        srgb_r, srgb_g, srgb_b = hsv_to_srgb(hsb_hue, hsb_sat, hsb_bri)

        # Convert sRGB to OKLCH for storage
        oklch_l, oklch_c, oklch_h = srgb_to_oklch(srgb_r, srgb_g, srgb_b)

        # Create ColorValue
        color = ColorValue(
            level=level,
            oklch_l=oklch_l,
            oklch_c=oklch_c,
            oklch_h=oklch_h,
        )

        # Store sRGB values
        color.srgb_r = srgb_r
        color.srgb_g = srgb_g
        color.srgb_b = srgb_b
        color.srgb_in_gamut = True  # HSB always produces in-gamut sRGB

        # Compute P3 values (same as sRGB for HSB-derived colors)
        # But we recalculate from OKLCH for consistency
        p3_r, p3_g, p3_b, p3_in_gamut = oklch_to_p3(oklch_l, oklch_c, oklch_h)
        color.p3_r = p3_r
        color.p3_g = p3_g
        color.p3_b = p3_b
        color.p3_in_gamut = p3_in_gamut

        scale.colors[level] = color

    return scale


def chroma_envelope(t: float, min_ratio: float = 0.15) -> float:
    """
    Chroma envelope that peaks at t=0.5, tapers toward min_ratio at t=0 and t=1.

    Creates natural-looking scales where:
    - Level 50 (t=0): Near white, retains subtle hue tint (min_ratio of peak)
    - Level 500 (t=0.5): Peak chroma (1.0)
    - Level 950 (t=1): Near black, retains subtle hue tint (min_ratio of peak)

    Args:
        t: Position in scale (0 to 1)
        min_ratio: Minimum chroma as ratio of peak (default 0.15 = 15%)
    """
    # sin curve scaled to range from min_ratio to 1.0
    return min_ratio + (1.0 - min_ratio) * math.sin(t * math.pi)


# ========== Color Data Structures ==========


@dataclass
class ColorValue:
    """A single color at a specific level."""

    level: int
    oklch_l: float
    oklch_c: float
    oklch_h: float

    # P3 values (always computed)
    p3_r: float = 0.0
    p3_g: float = 0.0
    p3_b: float = 0.0
    p3_in_gamut: bool = True

    # sRGB fallback
    srgb_r: float = 0.0
    srgb_g: float = 0.0
    srgb_b: float = 0.0
    srgb_in_gamut: bool = True
    srgb_was_clipped: bool = False

    # APCA contrast values
    apca_vs_light_bg: Optional[float] = None  # vs neutral-50
    apca_vs_dark_bg: Optional[float] = None  # vs neutral-950

    @property
    def hex_p3(self) -> str:
        """Hex string for P3 (note: this is technically wrong for OOG colors)."""
        return hex_from_rgb01(self.p3_r, self.p3_g, self.p3_b)

    @property
    def hex_srgb(self) -> str:
        """Hex string for sRGB."""
        return hex_from_rgb01(self.srgb_r, self.srgb_g, self.srgb_b)

    @property
    def css_p3(self) -> str:
        """CSS color(display-p3) string."""
        return css_p3_string(self.p3_r, self.p3_g, self.p3_b)

    @property
    def css_oklch(self) -> str:
        """CSS oklch() string."""
        return f"oklch({self.oklch_l:.2%} {self.oklch_c:.4f} {self.oklch_h:.1f})"


@dataclass
class ColorScale:
    """A full 11-step scale for a single hue."""

    name: str
    oklch_hue: float
    colors: Dict[int, ColorValue] = field(default_factory=dict)

    def get_hex_list(self, gamut: Gamut = "p3") -> List[str]:
        """Get list of hex values in level order."""
        result = []
        for level in LEVELS:
            color = self.colors.get(level)
            if color:
                result.append(color.hex_p3 if gamut == "p3" else color.hex_srgb)
        return result


@dataclass
class Palette:
    """Complete palette with all scales."""

    scales: Dict[str, ColorScale] = field(default_factory=dict)
    chroma_mode: ChromaMode = "even"
    gamut: Gamut = "p3"

    # Neutral backgrounds for APCA (sRGB values)
    neutral_light_bg: Optional[Tuple[float, float, float]] = None  # neutral-50 sRGB
    neutral_dark_bg: Optional[Tuple[float, float, float]] = None  # neutral-950 sRGB

    # Neutral backgrounds for APCA (P3 values) - used when gamut="p3"
    neutral_light_bg_p3: Optional[Tuple[float, float, float]] = None  # neutral-50 P3
    neutral_dark_bg_p3: Optional[Tuple[float, float, float]] = None  # neutral-950 P3


# ========== Palette Name Mapping ==========

# Maps brandcolor.py names to palette.py positional names
NAME_MAPPING = {
    "base": "primary",
    "adjacent_left": "analogous-cool",
    "adjacent_right": "analogous-warm",
    "complementary": "complement",
    "triad_left": "split-complement-cool",
    "triad_right": "split-complement-warm",
}


def map_name(brandcolor_name: str) -> str:
    """Convert brandcolor.py name to palette.py positional name."""
    return NAME_MAPPING.get(brandcolor_name, brandcolor_name)


# ========== Scale Generation ==========


def generate_lightness(t: float) -> float:
    """
    Generate lightness value for position t using easeInOutQuad.

    L range: 0.96 (level 50) -> 0.25 (level 950)

    Note: L_DARK=0.25 (vs 0.15) matches ColorBox output where darkest
    colors retain visible hue. L=0.15 produces near-black with lost color.
    """
    L_LIGHT = 0.96
    L_DARK = 0.25
    return L_LIGHT - (L_LIGHT - L_DARK) * ease_in_out_quad(t)


def find_anchor_level(anchor_L: float) -> Tuple[int, float]:
    """
    Find the level (50-950) whose default lightness best matches anchor_L.

    Args:
        anchor_L: Target lightness value (0-1)

    Returns:
        (level, t) - The level number and its position t (0-1)
    """
    best_level = 500
    best_t = 0.5
    best_diff = float("inf")

    for level, t in LEVEL_TO_T.items():
        default_L = generate_lightness(t)
        diff = abs(default_L - anchor_L)
        if diff < best_diff:
            best_diff = diff
            best_level = level
            best_t = t

    return best_level, best_t


def generate_lightness_anchored(
    t: float,
    anchor_L: float,
    anchor_t: float,
    power: float = 1.5,
) -> float:
    """
    Generate lightness that passes through anchor_L at anchor_t.

    Uses piecewise power-curve interpolation calibrated to match ColorBox output:
    - t in [0, anchor_t]: easeIn with configurable power (t^power)
    - t in [anchor_t, 1]: easeOut with same power (1-(1-t)^power)

    The default power of 1.6 was derived by analyzing ColorBox's actual output.
    ColorBox uses HSB which maps non-linearly to OKLCH lightness, resulting in
    a "lazier" curve than standard easeInOutQuad (power=2.0).

    Args:
        t: Current position (0-1)
        anchor_L: Lightness at anchor point
        anchor_t: Position of anchor (0-1)
        power: Easing power (default 1.6 matches ColorBox; 2.0 = quad)

    Returns:
        Lightness value at position t
    """
    L_LIGHT = 0.96  # Level 50 (provides more chroma headroom)
    L_DARK = 0.25  # Level 950 (ColorBox: 0.25 retains visible hue)

    if anchor_t < 1e-9:
        # Anchor at extreme light end
        if t < 1e-9:
            return anchor_L
        local_t = t / 1.0
        # easeOut for full range
        eased = 1.0 - pow(1.0 - local_t, power)
        return anchor_L + (L_DARK - anchor_L) * eased

    if anchor_t > 1.0 - 1e-9:
        # Anchor at extreme dark end
        if t > 1.0 - 1e-9:
            return anchor_L
        local_t = t / 1.0
        # easeIn for full range
        eased = pow(local_t, power)
        return L_LIGHT + (anchor_L - L_LIGHT) * eased

    if t <= anchor_t:
        # Interpolate from light end to anchor using easeIn
        local_t = t / anchor_t
        eased = pow(local_t, power)
        return L_LIGHT + (anchor_L - L_LIGHT) * eased
    else:
        # Interpolate from anchor to dark end using easeOut
        local_t = (t - anchor_t) / (1.0 - anchor_t)
        eased = 1.0 - pow(1.0 - local_t, power)
        return anchor_L + (L_DARK - anchor_L) * eased


def generate_chroma_anchored(
    t: float,
    anchor_C: float,
    anchor_t: float,
    min_ratio: float = 0.15,
) -> float:
    """
    Generate chroma that peaks at anchor_C at anchor_t.

    The envelope is shifted so the peak occurs at anchor_t rather than t=0.5.
    Chroma tapers to min_ratio * anchor_C at both ends.

    Args:
        t: Current position (0-1)
        anchor_C: Chroma at anchor point (the peak)
        anchor_t: Position of anchor (0-1)
        min_ratio: Minimum chroma ratio at extremes (default 0.15)

    Returns:
        Chroma value at position t
    """
    if anchor_t < 1e-9 or anchor_t > 1.0 - 1e-9:
        # Anchor at extreme - use simple linear taper
        if t <= anchor_t:
            return anchor_C
        else:
            local_t = (t - anchor_t) / (1.0 - anchor_t) if anchor_t < 0.5 else t
            return anchor_C * (1.0 - (1.0 - min_ratio) * local_t)

    # Piecewise envelope peaking at anchor_t
    if t <= anchor_t:
        # Rise from min to peak
        local_t = t / anchor_t
        envelope = min_ratio + (1.0 - min_ratio) * math.sin(local_t * math.pi / 2)
    else:
        # Fall from peak to min
        local_t = (t - anchor_t) / (1.0 - anchor_t)
        envelope = min_ratio + (1.0 - min_ratio) * math.cos(local_t * math.pi / 2)

    return anchor_C * envelope


def generate_hue_shifted(
    t: float,
    anchor_H: float,
    anchor_t: float,
    light_shift: float = -16.0,
    dark_shift: float = 31.0,
) -> float:
    """
    Generate hue that shifts across the scale while pinning anchor exactly.

    Based on ColorBox analysis:
    - Light side shifts toward cooler (cyan direction): -16° at level 50
    - Dark side shifts toward warmer (blue direction): +31° at level 950
    - Light side uses easeOut (fast decay) to reach anchor hue earlier
    - Dark side uses easeIn (accelerating shift) toward blue

    Args:
        t: Current position (0-1)
        anchor_H: Hue at anchor point (degrees)
        anchor_t: Position of anchor (0-1)
        light_shift: Hue shift at light end (default -16° toward cyan)
        dark_shift: Hue shift at dark end (default +31° toward blue)

    Returns:
        Hue in degrees (0-360)
    """
    if t <= anchor_t:
        # Light side: shift from light_shift toward 0
        # Use easeOut (power 2.2) for faster decay - matches ColorBox pattern
        # where hue reaches anchor value around mid-tones
        if anchor_t > 1e-9:
            local_t = t / anchor_t
            # easeOut: remaining shift decays as (1-t)^2.2
            remaining = pow(1.0 - local_t, 2.2)
            shift = light_shift * remaining
        else:
            shift = 0.0
    else:
        # Dark side: shift from 0 toward dark_shift
        if anchor_t < 1.0 - 1e-9:
            local_t = (t - anchor_t) / (1.0 - anchor_t)
            # Gentle easeOut (power 0.9) - ColorBox shifts early then slows
            eased = pow(local_t, 0.9)
            shift = dark_shift * eased
        else:
            shift = 0.0

    return mod360(anchor_H + shift)


def generate_chroma_colorbox(
    t: float,
    anchor_C: float,
    anchor_t: float,
    L: float,
    H: float,
    gamut: Gamut = "p3",
) -> float:
    """
    Generate chroma using ColorBox-style distribution.

    Based on reverse-engineering ColorBox output, the chroma pattern is:
    - Level 50 (t=0): 100% of gamut (gamut is tiny at L=0.96)
    - Level 200 (t=0.2): ~53% of gamut (dip in the upper-middle)
    - Level 400 (t=0.4): Peak absolute chroma (mid-tones are richest)
    - Level 700 (t=0.7): Anchor value preserved exactly
    - Level 950 (t=1.0): 100% of gamut (gamut is small at L=0.25)

    The % of gamut forms a U-shape because gamut varies with lightness,
    but absolute chroma forms a bell curve peaking at mid-tones.

    Args:
        t: Current position (0-1)
        anchor_C: Chroma at anchor point
        anchor_t: Position of anchor (0-1)
        L: Lightness at this position (for gamut calculation)
        H: Hue at this position (for gamut calculation)
        gamut: Target gamut for max chroma calculation

    Returns:
        Chroma value
    """
    # Exact anchor case - return anchor_C directly
    if abs(t - anchor_t) < 1e-9:
        return anchor_C

    # Get max chroma at this L, H
    c_max = cmax_for_L_h(L, H, gamut) * 0.99  # 99% for safety

    # ColorBox chroma pattern (% of gamut):
    # - t=0: 100%
    # - t=0.1: 79%
    # - t=0.2: 53% (minimum)
    # - t=0.3: 64%
    # - t=0.4: 76%
    # - t=0.5: 86%
    # - t=0.6: 94%
    # - t=0.7+: 100%
    #
    # Model as piecewise:
    # [0, 0.2]: Drop from 100% to 53% (easeIn)
    # [0.2, 0.7]: Rise from 53% to 100% (gentle power curve t^0.8)
    # [0.7, 1.0]: Stay at 100%

    if t <= 0.2:
        # Drop from 100% to 53% using gentle power curve
        # t^1.2 matches ColorBox's 100% -> 79% -> 53% pattern
        local_t = t / 0.2
        ratio = 1.0 - (1.0 - 0.53) * pow(local_t, 1.2)
    elif t <= 0.7:
        # Rise from 53% to 100% using gentle power curve
        # t^0.8 matches ColorBox's gradual rise better than easeOutQuad
        local_t = (t - 0.2) / 0.5
        ratio = 0.53 + (1.0 - 0.53) * pow(local_t, 0.8)
    else:
        # Stay at 100%
        ratio = 1.0

    # Scale the ratio so that at anchor_t we get anchor_C
    # First, compute what ratio we'd get at anchor_t with this curve
    if anchor_t <= 0.2:
        local_t = anchor_t / 0.2
        anchor_curve_ratio = 1.0 - (1.0 - 0.53) * ease_in_quad(local_t)
    elif anchor_t <= 0.7:
        local_t = (anchor_t - 0.2) / 0.5
        anchor_curve_ratio = 0.53 + (1.0 - 0.53) * ease_out_quad(local_t)
    else:
        anchor_curve_ratio = 1.0

    # Compute anchor's c_max
    anchor_L_approx = generate_lightness(anchor_t)
    anchor_c_max = cmax_for_L_h(anchor_L_approx, H, gamut) * 0.99

    # What chroma would the curve produce at anchor?
    curve_c_at_anchor = anchor_curve_ratio * anchor_c_max

    # Scale factor to hit anchor_C exactly
    if curve_c_at_anchor > 1e-9:
        scale = anchor_C / curve_c_at_anchor
    else:
        scale = 1.0

    # Apply scaled ratio
    C = ratio * c_max * scale

    # Ensure we don't exceed gamut
    return min(C, c_max)


def generate_neutral_chroma(
    t: float,
    max_chroma: float = 0.10,
    min_chroma: float = 0.0,
) -> float:
    """
    Generate chroma for neutral scale using easeIn.

    Clean whites (low chroma at light end), visibly tinted darks.
    ColorBox uses 0 → 0.9 HSB saturation which translates to noticeable
    hue tinting throughout the neutral scale.

    Args:
        t: Position (0-1)
        max_chroma: Maximum chroma at dark end (default 0.10)
                    Increased from 0.04 to match ColorBox's visible tinting.
        min_chroma: Minimum chroma at light end (default 0.0)

    Returns:
        Chroma value
    """
    return min_chroma + (max_chroma - min_chroma) * ease_in_quad(t)


def generate_color_chroma(
    t: float,
    base_chroma: float,
) -> float:
    """
    Generate color chroma using envelope that peaks at mid-tones.
    """
    return base_chroma * chroma_envelope(t)


def compute_scale(
    name: str,
    oklch_hue: float,
    chroma_at_peak: float,
    gamut: Gamut,
    is_neutral: bool = False,
    neutral_max_chroma: float = 0.10,
) -> ColorScale:
    """
    Generate a complete 11-step color scale.

    Args:
        name: Scale name (e.g., "primary", "neutral")
        oklch_hue: OKLCH hue angle
        chroma_at_peak: Maximum chroma at level 500 (ignored for neutrals)
        gamut: Target gamut ("p3" or "srgb")
        is_neutral: If True, use neutral chroma curve instead
        neutral_max_chroma: Max chroma for neutrals at level 950

    Returns:
        ColorScale with all 11 levels computed
    """
    scale = ColorScale(name=name, oklch_hue=oklch_hue)

    # Neutrals go darker (near-black) at 950; colors stay at 0.25 for visible hue
    L_LIGHT = 0.96
    L_DARK_NEUTRAL = 0.12  # Near-black for neutrals
    L_DARK_COLOR = 0.25  # Retains visible hue for colors

    for level in LEVELS:
        t = LEVEL_TO_T[level]

        # Compute L - neutrals go darker than colors
        if is_neutral:
            L = L_LIGHT - (L_LIGHT - L_DARK_NEUTRAL) * ease_in_out_quad(t)
        else:
            L = generate_lightness(t)  # Uses L_DARK=0.25

        if is_neutral:
            C = generate_neutral_chroma(t, neutral_max_chroma)
        else:
            C = generate_color_chroma(t, chroma_at_peak)

        # Create color value
        color = ColorValue(
            level=level,
            oklch_l=L,
            oklch_c=C,
            oklch_h=oklch_hue,
        )

        # Compute P3 values
        p3_r, p3_g, p3_b, p3_in_gamut = oklch_to_p3(L, C, oklch_hue)
        color.p3_r = p3_r
        color.p3_g = p3_g
        color.p3_b = p3_b
        color.p3_in_gamut = p3_in_gamut

        # If out of P3 gamut, reduce chroma
        if not p3_in_gamut:
            c_max = cmax_for_L_h(L, oklch_hue, "p3") * 0.98
            C = min(C, c_max)
            color.oklch_c = C
            p3_r, p3_g, p3_b, _ = oklch_to_p3(L, C, oklch_hue)
            color.p3_r = p3_r
            color.p3_g = p3_g
            color.p3_b = p3_b
            color.p3_in_gamut = True

        # Compute sRGB fallback
        srgb_r, srgb_g, srgb_b, srgb_in_gamut = oklch_to_srgb(L, C, oklch_hue)
        color.srgb_r = srgb_r
        color.srgb_g = srgb_g
        color.srgb_b = srgb_b
        color.srgb_in_gamut = srgb_in_gamut

        # If sRGB needs clipping (P3 color outside sRGB), note it
        if not srgb_in_gamut:
            color.srgb_was_clipped = True

        scale.colors[level] = color

    return scale


def compute_scale_anchored(
    name: str,
    anchor_L: float,
    anchor_C: float,
    anchor_H: float,
    anchor_level: int,
    gamut: Gamut,
) -> ColorScale:
    """
    Generate a color scale anchored at specific L, C, H values.

    The anchor color appears EXACTLY at anchor_level. Other levels
    are interpolated using anchored lightness and chroma curves.

    Args:
        name: Scale name (e.g., "primary")
        anchor_L: Anchor lightness (0-1)
        anchor_C: Anchor chroma (0-0.37)
        anchor_H: Anchor hue (degrees)
        anchor_level: Level to place anchor at (50-950)
        gamut: Target gamut ("p3" or "srgb")

    Returns:
        ColorScale with anchor at specified level
    """
    scale = ColorScale(name=name, oklch_hue=anchor_H)
    anchor_t = LEVEL_TO_T[anchor_level]

    for level in LEVELS:
        t = LEVEL_TO_T[level]

        if level == anchor_level:
            # Use EXACT anchor values
            L, C = anchor_L, anchor_C
        else:
            # Generate from anchored curves
            L = generate_lightness_anchored(t, anchor_L, anchor_t)
            C = generate_chroma_anchored(t, anchor_C, anchor_t)

        H = anchor_H

        # Create color value
        color = ColorValue(
            level=level,
            oklch_l=L,
            oklch_c=C,
            oklch_h=H,
        )

        # Compute P3 values
        p3_r, p3_g, p3_b, p3_in_gamut = oklch_to_p3(L, C, H)
        color.p3_r, color.p3_g, color.p3_b = p3_r, p3_g, p3_b
        color.p3_in_gamut = p3_in_gamut

        # Gamut clipping for non-anchor levels
        if not p3_in_gamut and level != anchor_level:
            c_max = cmax_for_L_h(L, H, "p3") * 0.98
            C = min(C, c_max)
            color.oklch_c = C
            p3_r, p3_g, p3_b, _ = oklch_to_p3(L, C, H)
            color.p3_r, color.p3_g, color.p3_b = p3_r, p3_g, p3_b
            color.p3_in_gamut = True

        # Compute sRGB fallback
        srgb_r, srgb_g, srgb_b, srgb_in_gamut = oklch_to_srgb(L, C, H)
        color.srgb_r, color.srgb_g, color.srgb_b = srgb_r, srgb_g, srgb_b
        color.srgb_in_gamut = srgb_in_gamut
        if not srgb_in_gamut:
            color.srgb_was_clipped = True

        scale.colors[level] = color

    return scale


def compute_scale_colorbox(
    name: str,
    anchor_L: float,
    anchor_C: float,
    anchor_H: float,
    anchor_level: int,
    gamut: Gamut,
    hue_shift: bool = True,
    light_hue_shift: float = -16.0,
    dark_hue_shift: float = 31.0,
) -> ColorScale:
    """
    Generate a color scale using ColorBox-style curves.

    Features:
    - Bell-curve chroma peaking at mid-tones (level 400)
    - Asymmetric hue shifting (cooler lights, warmer/bluer darks)
    - Exact anchor placement - brand color preserved
    - Lightness range 0.96 → 0.25 (visible color in darks)

    Args:
        name: Scale name (e.g., "primary")
        anchor_L: Anchor lightness (0-1)
        anchor_C: Anchor chroma (0-0.37)
        anchor_H: Anchor hue (degrees)
        anchor_level: Level to place anchor at (50-950)
        gamut: Target gamut ("p3" or "srgb")
        hue_shift: Whether to shift hue across scale
        light_hue_shift: Hue shift at light end (default -16° toward cyan)
        dark_hue_shift: Hue shift at dark end (default +31° toward blue)

    Returns:
        ColorScale with ColorBox-style curves
    """
    scale = ColorScale(name=name, oklch_hue=anchor_H)
    anchor_t = LEVEL_TO_T[anchor_level]

    for level in LEVELS:
        t = LEVEL_TO_T[level]

        if level == anchor_level:
            # Use EXACT anchor values
            L, C, H = anchor_L, anchor_C, anchor_H
        else:
            # Generate lightness (piecewise easeInOut through anchor)
            L = generate_lightness_anchored(t, anchor_L, anchor_t)

            # Generate hue with optional asymmetric shift
            if hue_shift:
                H = generate_hue_shifted(
                    t, anchor_H, anchor_t, light_hue_shift, dark_hue_shift
                )
            else:
                H = anchor_H

            # Generate chroma using ColorBox bell-curve pattern
            C = generate_chroma_colorbox(t, anchor_C, anchor_t, L, H, gamut)

        # Create color value
        color = ColorValue(
            level=level,
            oklch_l=L,
            oklch_c=C,
            oklch_h=H,
        )

        # Compute P3 values
        p3_r, p3_g, p3_b, p3_in_gamut = oklch_to_p3(L, C, H)
        color.p3_r, color.p3_g, color.p3_b = p3_r, p3_g, p3_b
        color.p3_in_gamut = p3_in_gamut

        # Gamut clipping for non-anchor levels
        if not p3_in_gamut and level != anchor_level:
            c_max = cmax_for_L_h(L, H, "p3") * 0.98
            C = min(C, c_max)
            color.oklch_c = C
            p3_r, p3_g, p3_b, _ = oklch_to_p3(L, C, H)
            color.p3_r, color.p3_g, color.p3_b = p3_r, p3_g, p3_b
            color.p3_in_gamut = True

        # Compute sRGB fallback
        srgb_r, srgb_g, srgb_b, srgb_in_gamut = oklch_to_srgb(L, C, H)
        color.srgb_r, color.srgb_g, color.srgb_b = srgb_r, srgb_g, srgb_b
        color.srgb_in_gamut = srgb_in_gamut
        if not srgb_in_gamut:
            color.srgb_was_clipped = True

        scale.colors[level] = color

    return scale


def compute_even_chroma(
    hues: List[float],
    gamut: Gamut,
) -> float:
    """
    Find the minimum max-chroma across all hues at peak lightness (L=0.55).

    This ensures all hues can achieve the same chroma level.
    """
    L_peak = generate_lightness(0.5)  # Level 500

    min_cmax = float("inf")
    for h in hues:
        cmax = cmax_for_L_h(L_peak, h, gamut)
        min_cmax = min(min_cmax, cmax)

    # Apply safety margin
    return min_cmax * 0.95


# ========== Palette Building ==========


def build_ryb_palette_hues(
    H_base_ryb: float,
    mode: str,
    x_deg: float,
    include_comp: bool,
) -> List[Tuple[str, float]]:
    """
    Build list of (label, RYB hue) for the palette.

    Mirrors brandcolor.py logic but with new names.
    """
    parts: List[Tuple[str, float]] = [("primary", mod360(H_base_ryb))]

    if mode in ("adjacent", "full"):
        parts.append(("analogous-cool", mod360(H_base_ryb - x_deg)))
        parts.append(("analogous-warm", mod360(H_base_ryb + x_deg)))

    if include_comp:
        parts.append(("complement", mod360(H_base_ryb + 180.0)))

    if mode in ("triad", "full"):
        parts.append(("split-complement-cool", mod360(H_base_ryb + 180.0 - x_deg)))
        parts.append(("split-complement-warm", mod360(H_base_ryb + 180.0 + x_deg)))

    # Dedupe by hue
    out: List[Tuple[str, float]] = []
    seen: List[float] = []
    for lab, h in parts:
        if not any(abs(((h - s + 540.0) % 360.0) - 180.0) < 1e-7 for s in seen):
            out.append((lab, h))
            seen.append(h)

    return out


def generate_palette(
    hue_weights: List[Tuple[str, float]],  # [(name, weight), ...]
    chroma_mode: ChromaMode,
    gamut: Gamut,
    palette_set: str = "full",
    x_deg: float = 30.0,
    include_complementary: bool = False,
    neutral_max_chroma: float = 0.10,
) -> Palette:
    """
    Generate a complete palette from hue weights.

    Args:
        hue_weights: List of (hue_name, weight) from RYB anchors
        chroma_mode: "even", "max", or "both"
        gamut: "p3" or "srgb"
        palette_set: "base", "adjacent", "triad", or "full"
        x_deg: Angle for adjacent/triad offsets
        include_complementary: Include complement hue
        neutral_max_chroma: Max chroma for darkest neutral

    Returns:
        Palette with all scales computed
    """
    # Compute weighted primary RYB hue
    hues_deg = [RYB_ANCHOR_DEG[name] for name, _ in hue_weights]
    weights = [w for _, w in hue_weights]
    H_ryb = circular_mean_deg(hues_deg, weights)

    # Build palette hues (RYB)
    ryb_hues = build_ryb_palette_hues(H_ryb, palette_set, x_deg, include_complementary)

    # Convert to OKLCH hues and get HSB hues
    oklch_hues: List[Tuple[str, float]] = []
    hsb_hues: List[Tuple[str, float]] = []
    for name, h_ryb in ryb_hues:
        h_rgb = ryb_hue_to_rgb_hue(h_ryb)  # RGB hue = HSB hue
        h_oklch = rgb_hue_to_oklch_hue_deg(h_rgb)
        oklch_hues.append((name, h_oklch))
        hsb_hues.append((name, h_rgb))

    # Primary HSB hue for ColorBox neutral generation
    primary_hsb_hue = hsb_hues[0][1] if hsb_hues else 0.0

    # Create palette
    palette = Palette(chroma_mode=chroma_mode, gamut=gamut)

    # Step 1: Generate neutrals using ColorBox algorithm
    # ColorBox settings: Hue ±15° easeOut, Sat 0→0.9 easeIn, Bri 0.99→0.1 easeInOut
    neutral_scale = compute_neutral_scale_colorbox(
        base_hsb_hue=primary_hsb_hue,
        gamut=gamut,
        hue_shift=15.0,
        sat_start=0.0,
        sat_end=0.9,
        bri_start=0.99,
        bri_end=0.10,
    )
    palette.scales["neutral"] = neutral_scale

    # Extract neutral backgrounds for APCA (both sRGB and P3)
    neutral_50 = neutral_scale.colors[50]
    neutral_950 = neutral_scale.colors[950]
    palette.neutral_light_bg = (neutral_50.srgb_r, neutral_50.srgb_g, neutral_50.srgb_b)
    palette.neutral_dark_bg = (
        neutral_950.srgb_r,
        neutral_950.srgb_g,
        neutral_950.srgb_b,
    )
    palette.neutral_light_bg_p3 = (neutral_50.p3_r, neutral_50.p3_g, neutral_50.p3_b)
    palette.neutral_dark_bg_p3 = (neutral_950.p3_r, neutral_950.p3_g, neutral_950.p3_b)

    # Step 2: Compute chroma for color scales
    all_oklch_hues = [h for _, h in oklch_hues]

    if chroma_mode == "even":
        even_chroma = compute_even_chroma(all_oklch_hues, gamut)
        chroma_values = {name: even_chroma for name, _ in oklch_hues}
    elif chroma_mode == "max":
        L_peak = generate_lightness(0.5)
        chroma_values = {
            name: cmax_for_L_h(L_peak, h, gamut) * 0.95 for name, h in oklch_hues
        }
    else:  # "both" - we'll generate two sets
        even_chroma = compute_even_chroma(all_oklch_hues, gamut)
        L_peak = generate_lightness(0.5)
        # For "both", we return even mode; caller handles max separately
        chroma_values = {name: even_chroma for name, _ in oklch_hues}

    # Step 3: Generate color scales
    for name, h_oklch in oklch_hues:
        scale = compute_scale(
            name=name,
            oklch_hue=h_oklch,
            chroma_at_peak=chroma_values[name],
            gamut=gamut,
            is_neutral=False,
        )
        palette.scales[name] = scale

    # Step 4: Compute APCA contrast for all colors
    # Use gamut-appropriate values and coefficients
    for scale in palette.scales.values():
        for color in scale.colors.values():
            if gamut == "p3":
                # Use P3 values with P3 APCA coefficients
                color_rgb = (color.p3_r, color.p3_g, color.p3_b)
                light_bg = palette.neutral_light_bg_p3
                dark_bg = palette.neutral_dark_bg_p3
                color.apca_vs_light_bg = calc_apca_p3(color_rgb, light_bg)
                color.apca_vs_dark_bg = calc_apca_p3(color_rgb, dark_bg)
            else:
                # Use sRGB values with sRGB APCA coefficients
                color_rgb = (color.srgb_r, color.srgb_g, color.srgb_b)
                light_bg = palette.neutral_light_bg
                dark_bg = palette.neutral_dark_bg
                color.apca_vs_light_bg = calc_apca_from_rgb01(color_rgb, light_bg)
                color.apca_vs_dark_bg = calc_apca_from_rgb01(color_rgb, dark_bg)

    return palette


def generate_palette_from_brand_color(
    brand_result: "BrandColorResult",
    chroma_mode: Literal["even", "max"] = "even",
    gamut: Gamut = "p3",
    neutral_max_chroma: float = 0.10,
    hue_shift: bool = False,
    light_hue_shift: float = -16.0,
    dark_hue_shift: float = 31.0,
) -> Palette:
    """
    Generate palette from brandcolor.py result with ColorBox-style curves.

    Features:
    - Exact anchor placement at matched level
    - Bell-curve chroma (richest at mid-tones)
    - Optional hue shifting (cooler lights, bluer darks) - OFF by default
    - ColorBox-style tinted neutrals with hue rotation

    Args:
        brand_result: Output from compute_brand_colors()
        chroma_mode: "even" uses brand_result.C for all hues,
                     "max" computes per-hue max chroma at brand_result.L
        gamut: Target gamut
        neutral_max_chroma: Max chroma for neutral scale at level 950
                           (Note: ColorBox uses HSB saturation 0→0.9)
        hue_shift: Whether to shift hue across scale (default False)
        light_hue_shift: Hue shift at light end (default -16° toward cyan)
        dark_hue_shift: Hue shift at dark end (default +31° toward blue)

    Returns:
        Palette with all scales using ColorBox curves
    """
    palette = Palette(chroma_mode="anchored", gamut=gamut)

    # Find which level matches anchor L
    anchor_level, anchor_t = find_anchor_level(brand_result.L)

    # Get primary HSB hue for ColorBox neutral generation
    # Extract from the base color's sRGB values
    primary_label = brand_result.labels[0]  # "base"
    base_rgb = brand_result.srgb_values[primary_label]
    base_hsb_hue, _, _ = srgb_to_hsv(base_rgb[0], base_rgb[1], base_rgb[2])

    # Step 1: Generate neutral scale using ColorBox algorithm
    # ColorBox settings: Hue ±15° easeOut, Sat 0→0.9 easeIn, Bri 0.99→0.1 easeInOut
    neutral_scale = compute_neutral_scale_colorbox(
        base_hsb_hue=base_hsb_hue,
        gamut=gamut,
        hue_shift=15.0,
        sat_start=0.0,
        sat_end=0.9,
        bri_start=0.99,
        bri_end=0.10,
    )
    palette.scales["neutral"] = neutral_scale

    # Extract neutral backgrounds for APCA
    neutral_50 = neutral_scale.colors[50]
    neutral_950 = neutral_scale.colors[950]
    palette.neutral_light_bg = (neutral_50.srgb_r, neutral_50.srgb_g, neutral_50.srgb_b)
    palette.neutral_dark_bg = (
        neutral_950.srgb_r,
        neutral_950.srgb_g,
        neutral_950.srgb_b,
    )
    palette.neutral_light_bg_p3 = (neutral_50.p3_r, neutral_50.p3_g, neutral_50.p3_b)
    palette.neutral_dark_bg_p3 = (neutral_950.p3_r, neutral_950.p3_g, neutral_950.p3_b)

    # Step 2: Generate color scales with ColorBox curves
    # For "even" mode, compute minimum achievable chroma across all hues at anchor L
    # This ensures all hues can achieve the same chroma level
    if chroma_mode == "even":
        all_hues = [brand_result.oklch_hues[lab] for lab in brand_result.labels]
        min_cmax = float("inf")
        for h in all_hues:
            cmax = cmax_for_L_h(brand_result.L, h, gamut)
            min_cmax = min(min_cmax, cmax)
        even_chroma = min_cmax * 0.95  # Use minimum max chroma across all hues

    for label in brand_result.labels:
        oklch_hue = brand_result.oklch_hues[label]
        scale_name = map_name(label)  # "base" -> "primary", etc.

        # Determine chroma for this scale
        if chroma_mode == "max":
            # Use maximum safe chroma at anchor L for this hue
            anchor_C = cmax_for_L_h(brand_result.L, oklch_hue, gamut) * 0.95
        else:
            # Use even chroma (minimum across all harmonics)
            anchor_C = even_chroma

        scale = compute_scale_colorbox(
            name=scale_name,
            anchor_L=brand_result.L,
            anchor_C=anchor_C,
            anchor_H=oklch_hue,
            anchor_level=anchor_level,
            gamut=gamut,
            hue_shift=hue_shift,
            light_hue_shift=light_hue_shift,
            dark_hue_shift=dark_hue_shift,
        )
        palette.scales[scale_name] = scale

    # Step 3: Compute APCA contrast for all colors
    for scale in palette.scales.values():
        for color in scale.colors.values():
            if (
                gamut == "p3"
                and palette.neutral_light_bg_p3
                and palette.neutral_dark_bg_p3
            ):
                color_rgb = (color.p3_r, color.p3_g, color.p3_b)
                color.apca_vs_light_bg = calc_apca_p3(
                    color_rgb, palette.neutral_light_bg_p3
                )
                color.apca_vs_dark_bg = calc_apca_p3(
                    color_rgb, palette.neutral_dark_bg_p3
                )
            elif palette.neutral_light_bg and palette.neutral_dark_bg:
                color_rgb = (color.srgb_r, color.srgb_g, color.srgb_b)
                color.apca_vs_light_bg = calc_apca_from_rgb01(
                    color_rgb, palette.neutral_light_bg
                )
                color.apca_vs_dark_bg = calc_apca_from_rgb01(
                    color_rgb, palette.neutral_dark_bg
                )

    return palette


# ========== APCA Validation ==========


@dataclass
class ContrastIssue:
    """A contrast issue found during validation."""

    scale_name: str
    level: int
    background: str  # "light" or "dark"
    actual_lc: float
    required_lc: float


@dataclass
class ContrastAdjustment:
    """Record of an APCA contrast adjustment."""

    scale_name: str
    level: int
    background: str  # "light" or "dark"
    L_old: float
    L_new: float
    C_old: float
    C_new: float
    lc_old: float
    lc_new: float
    success: bool


def validate_palette_contrast(
    palette: Palette,
    min_lc: float = APCA_THRESHOLD_LARGE_TEXT,  # 60 by default
) -> List[ContrastIssue]:
    """
    Validate all colors meet minimum APCA contrast.

    Args:
        palette: The palette to validate
        min_lc: Minimum absolute Lc value required

    Returns:
        List of contrast issues found
    """
    issues: List[ContrastIssue] = []

    for scale_name, scale in palette.scales.items():
        if scale_name == "neutral":
            continue  # Skip neutrals (they ARE the background)

        for level, color in scale.colors.items():
            # Light levels (50-400) should contrast against dark background
            # Dark levels (600-950) should contrast against light background
            # Level 500 should work against both

            if level <= 400:
                # Check against dark background
                if color.apca_vs_dark_bg is not None:
                    if abs(color.apca_vs_dark_bg) < min_lc:
                        issues.append(
                            ContrastIssue(
                                scale_name=scale_name,
                                level=level,
                                background="dark",
                                actual_lc=abs(color.apca_vs_dark_bg),
                                required_lc=min_lc,
                            )
                        )

            if level >= 600:
                # Check against light background
                if color.apca_vs_light_bg is not None:
                    if abs(color.apca_vs_light_bg) < min_lc:
                        issues.append(
                            ContrastIssue(
                                scale_name=scale_name,
                                level=level,
                                background="light",
                                actual_lc=abs(color.apca_vs_light_bg),
                                required_lc=min_lc,
                            )
                        )

            if level == 500:
                # Check against both
                if color.apca_vs_light_bg is not None:
                    if abs(color.apca_vs_light_bg) < min_lc:
                        issues.append(
                            ContrastIssue(
                                scale_name=scale_name,
                                level=level,
                                background="light",
                                actual_lc=abs(color.apca_vs_light_bg),
                                required_lc=min_lc,
                            )
                        )
                if color.apca_vs_dark_bg is not None:
                    if abs(color.apca_vs_dark_bg) < min_lc:
                        issues.append(
                            ContrastIssue(
                                scale_name=scale_name,
                                level=level,
                                background="dark",
                                actual_lc=abs(color.apca_vs_dark_bg),
                                required_lc=min_lc,
                            )
                        )

    return issues


def print_contrast_report(issues: List[ContrastIssue], file=sys.stderr) -> None:
    """Print contrast issues as warnings."""
    if not issues:
        print("APCA: All colors meet contrast requirements.", file=file)
        return

    print(f"APCA: {len(issues)} contrast issue(s) found:", file=file)
    for issue in issues:
        print(
            f"  {issue.scale_name}-{issue.level}: "
            f"Lc {issue.actual_lc:.1f} < {issue.required_lc:.1f} "
            f"(vs {issue.background} bg)",
            file=file,
        )


def auto_adjust_palette_contrast(
    palette: Palette,
    min_lc: float = APCA_THRESHOLD_LARGE_TEXT,
    max_delta_l: float = 0.15,
) -> List[ContrastAdjustment]:
    """
    Auto-adjust colors failing APCA contrast.

    Modifies palette in place. Returns list of adjustments made.
    """
    from color_utils import auto_adjust_for_contrast

    adjustments: List[ContrastAdjustment] = []

    for scale_name, scale in palette.scales.items():
        if scale_name == "neutral":
            continue

        for level, color in scale.colors.items():
            # Determine which background to check and direction
            checks = []

            # Select appropriate backgrounds based on gamut
            if palette.gamut == "p3":
                light_bg = palette.neutral_light_bg_p3
                dark_bg = palette.neutral_dark_bg_p3
            else:
                light_bg = palette.neutral_light_bg
                dark_bg = palette.neutral_dark_bg

            if level <= 400:
                # Light colors: check vs dark bg, adjust lighter if needed
                if color.apca_vs_dark_bg is not None:
                    if abs(color.apca_vs_dark_bg) < min_lc:
                        checks.append(("dark", dark_bg, "lighter"))

            if level >= 600:
                # Dark colors: check vs light bg, adjust darker if needed
                if color.apca_vs_light_bg is not None:
                    if abs(color.apca_vs_light_bg) < min_lc:
                        checks.append(("light", light_bg, "darker"))

            if level == 500:
                # Mid-tone: check both, prefer adjustment that works
                if color.apca_vs_light_bg is not None:
                    if abs(color.apca_vs_light_bg) < min_lc:
                        checks.append(("light", light_bg, "darker"))
                if color.apca_vs_dark_bg is not None:
                    if abs(color.apca_vs_dark_bg) < min_lc:
                        checks.append(("dark", dark_bg, "lighter"))

            for bg_name, bg_rgb, direction in checks:
                L_old = color.oklch_l
                C_old = color.oklch_c
                apca_value = (
                    color.apca_vs_dark_bg
                    if bg_name == "dark"
                    else color.apca_vs_light_bg
                )
                lc_old = abs(apca_value) if apca_value is not None else 0.0

                L_new, C_new, _, lc_new, success = auto_adjust_for_contrast(
                    L=color.oklch_l,
                    C=color.oklch_c,
                    H=color.oklch_h,
                    bg_rgb=bg_rgb,
                    min_lc=min_lc,
                    direction=direction,
                    gamut=palette.gamut,
                    max_delta_l=max_delta_l,
                )

                if L_new != L_old or C_new != C_old:
                    # Update color values
                    color.oklch_l = L_new
                    color.oklch_c = C_new

                    # Recompute P3/sRGB values
                    p3_r, p3_g, p3_b, p3_in = oklch_to_p3(L_new, C_new, color.oklch_h)
                    color.p3_r, color.p3_g, color.p3_b = p3_r, p3_g, p3_b
                    color.p3_in_gamut = p3_in

                    srgb_r, srgb_g, srgb_b, srgb_in = oklch_to_srgb(
                        L_new, C_new, color.oklch_h
                    )
                    color.srgb_r, color.srgb_g, color.srgb_b = srgb_r, srgb_g, srgb_b
                    color.srgb_in_gamut = srgb_in

                    # Recompute APCA using gamut-appropriate method
                    if palette.gamut == "p3":
                        color.apca_vs_light_bg = calc_apca_p3(
                            (color.p3_r, color.p3_g, color.p3_b),
                            palette.neutral_light_bg_p3,
                        )
                        color.apca_vs_dark_bg = calc_apca_p3(
                            (color.p3_r, color.p3_g, color.p3_b),
                            palette.neutral_dark_bg_p3,
                        )
                    else:
                        color.apca_vs_light_bg = calc_apca_from_rgb01(
                            (color.srgb_r, color.srgb_g, color.srgb_b),
                            palette.neutral_light_bg,
                        )
                        color.apca_vs_dark_bg = calc_apca_from_rgb01(
                            (color.srgb_r, color.srgb_g, color.srgb_b),
                            palette.neutral_dark_bg,
                        )

                    adjustments.append(
                        ContrastAdjustment(
                            scale_name=scale_name,
                            level=level,
                            background=bg_name,
                            L_old=L_old,
                            L_new=L_new,
                            C_old=C_old,
                            C_new=C_new,
                            lc_old=lc_old,
                            lc_new=lc_new,
                            success=success,
                        )
                    )

    return adjustments


def print_adjustment_report(
    adjustments: List[ContrastAdjustment], file=sys.stderr
) -> None:
    """Print APCA adjustments to stderr."""
    if not adjustments:
        return

    for adj in adjustments:
        status = "" if adj.success else " [FAILED]"
        print(
            f"APCA: Adjusted {adj.scale_name}-{adj.level} "
            f"L: {adj.L_old:.2f} -> {adj.L_new:.2f} "
            f"(Lc: {adj.lc_old:.1f} -> {adj.lc_new:.1f}){status}",
            file=file,
        )


# ========== Output Formatting ==========


def format_palette_block(palette: Palette, gamut: Gamut = "p3") -> str:
    """
    Format palette as markdown code block.

    Each line: name: hex1, hex2, hex3, ... (11 values, 50->950)
    """
    lines = ["```palette"]

    # Order: primary first, then others, neutral last
    scale_order = [
        "primary",
        "analogous-cool",
        "analogous-warm",
        "complement",
        "split-complement-cool",
        "split-complement-warm",
        "neutral",
    ]

    for name in scale_order:
        if name in palette.scales:
            scale = palette.scales[name]
            hex_list = scale.get_hex_list(gamut)
            lines.append(f"{name}: {', '.join(hex_list)}")

    # Add any other scales not in the order
    for name in palette.scales:
        if name not in scale_order:
            scale = palette.scales[name]
            hex_list = scale.get_hex_list(gamut)
            lines.append(f"{name}: {', '.join(hex_list)}")

    lines.append("```")
    return "\n".join(lines)


def format_tailwind_config(palette: Palette, use_oklch: bool = True) -> str:
    """
    Format palette as Tailwind CSS config.

    Uses oklch() for modern Tailwind, or hex for compatibility.
    """
    lines = [
        "module.exports = {",
        "  theme: {",
        "    colors: {",
    ]

    scale_order = [
        "primary",
        "analogous-cool",
        "analogous-warm",
        "complement",
        "split-complement-cool",
        "split-complement-warm",
        "neutral",
    ]

    def format_scale(name: str, scale: ColorScale) -> List[str]:
        # Handle names with hyphens for JS
        js_name = f"'{name}'" if "-" in name else name

        scale_lines = [f"      {js_name}: {{"]
        for level in LEVELS:
            color = scale.colors.get(level)
            if color:
                if use_oklch:
                    value = color.css_oklch
                else:
                    value = color.hex_srgb
                scale_lines.append(f"        {level}: '{value}',")
        scale_lines.append("      },")
        return scale_lines

    for name in scale_order:
        if name in palette.scales:
            lines.extend(format_scale(name, palette.scales[name]))

    for name in palette.scales:
        if name not in scale_order:
            lines.extend(format_scale(name, palette.scales[name]))

    lines.extend(
        [
            "    },",
            "  },",
            "};",
        ]
    )

    return "\n".join(lines)


def format_json(palette: Palette) -> str:
    """
    Format palette as JSON with full color data.

    Includes: oklch, p3, srgb, in_gamut flags, apca values
    """
    data = {
        "meta": {
            "chroma_mode": palette.chroma_mode,
            "gamut": palette.gamut,
        },
        "scales": {},
    }

    for name, scale in palette.scales.items():
        scale_data = {
            "oklch_hue": scale.oklch_hue,
            "levels": {},
        }

        for level, color in scale.colors.items():
            scale_data["levels"][str(level)] = {
                "oklch": {
                    "l": round(color.oklch_l, 4),
                    "c": round(color.oklch_c, 4),
                    "h": round(color.oklch_h, 2),
                },
                "p3": {
                    "hex": color.hex_p3,
                    "css": color.css_p3,
                    "in_gamut": color.p3_in_gamut,
                },
                "srgb": {
                    "hex": color.hex_srgb,
                    "in_gamut": color.srgb_in_gamut,
                    "was_clipped": color.srgb_was_clipped,
                },
                "apca": {
                    "vs_light_bg": (
                        round(color.apca_vs_light_bg, 1)
                        if color.apca_vs_light_bg is not None
                        else None
                    ),
                    "vs_dark_bg": (
                        round(color.apca_vs_dark_bg, 1)
                        if color.apca_vs_dark_bg is not None
                        else None
                    ),
                },
            }

        data["scales"][name] = scale_data

    return json.dumps(data, indent=2)


def format_css(palette: Palette, use_oklch: bool = True) -> str:
    """
    Format palette as CSS custom properties.

    Args:
        use_oklch: If True, use oklch() values; if False, use hex.

    Output:
        :root {
          /* Primary scale (hue: 264deg) */
          --color-primary-50: oklch(97.00% 0.0234 264.1);
          ...
        }
    """
    lines = [":root {"]

    scale_order = [
        "primary",
        "analogous-cool",
        "analogous-warm",
        "complement",
        "split-complement-cool",
        "split-complement-warm",
        "neutral",
    ]

    def format_scale(name: str, scale: ColorScale) -> List[str]:
        scale_lines = [
            f"  /* {name.title().replace('-', ' ')} scale (hue: {scale.oklch_hue:.0f}deg) */"
        ]
        for level in LEVELS:
            color = scale.colors.get(level)
            if color:
                if use_oklch:
                    value = color.css_oklch
                else:
                    value = color.hex_srgb
                scale_lines.append(f"  --color-{name}-{level}: {value};")
        scale_lines.append("")  # Blank line between scales
        return scale_lines

    for name in scale_order:
        if name in palette.scales:
            lines.extend(format_scale(name, palette.scales[name]))

    for name in palette.scales:
        if name not in scale_order:
            lines.extend(format_scale(name, palette.scales[name]))

    # Remove trailing blank line and close
    if lines[-1] == "":
        lines.pop()
    lines.append("}")

    return "\n".join(lines)


# ========== Visualization Functions ==========


def format_blocks(palette: Palette, gamut: Gamut = "p3", use_color: bool = True) -> str:
    """
    Format palette as colored block swatches.

    Output:
        primary:  ██ ██ ██ ██ ██ ██ ██ ██ ██ ██ ██
                  50 100 200 300 400 500 600 700 800 900 950
    """
    lines = []

    scale_order = [
        "primary",
        "analogous-cool",
        "analogous-warm",
        "complement",
        "split-complement-cool",
        "split-complement-warm",
        "neutral",
    ]

    for name in scale_order:
        if name not in palette.scales:
            continue
        scale = palette.scales[name]

        # Build blocks line
        blocks = []
        for level in LEVELS:
            color = scale.colors.get(level)
            if color:
                if gamut == "p3":
                    r, g, b = rgb01_to_255(color.p3_r, color.p3_g, color.p3_b)
                else:
                    r, g, b = rgb01_to_255(color.srgb_r, color.srgb_g, color.srgb_b)

                if use_color:
                    blocks.append(f"{rgb_bg(r, g, b)}  {RESET}")
                else:
                    blocks.append("##")

        # Build labels line
        labels = [f"{level:>3}" for level in LEVELS]

        lines.append(f"{name:>20}:  {' '.join(blocks)}")
        lines.append(f"{'':>20}   {' '.join(labels)}")
        lines.append("")

    return "\n".join(lines).rstrip()


def format_colored_text(
    palette: Palette, gamut: Gamut = "p3", use_color: bool = True
) -> str:
    """
    Format palette with hex values shown in their actual color.

    Output:
        primary: #F5F5F5 #EAEFFF #D4DFFE ...
    """
    lines = []

    scale_order = [
        "primary",
        "analogous-cool",
        "analogous-warm",
        "complement",
        "split-complement-cool",
        "split-complement-warm",
        "neutral",
    ]

    for name in scale_order:
        if name not in palette.scales:
            continue
        scale = palette.scales[name]

        hex_parts = []
        for level in LEVELS:
            color = scale.colors.get(level)
            if color:
                hex_val = color.hex_p3 if gamut == "p3" else color.hex_srgb
                if use_color:
                    if gamut == "p3":
                        r, g, b = rgb01_to_255(color.p3_r, color.p3_g, color.p3_b)
                    else:
                        r, g, b = rgb01_to_255(color.srgb_r, color.srgb_g, color.srgb_b)
                    hex_parts.append(f"{rgb_fg(r, g, b)}{hex_val}{RESET}")
                else:
                    hex_parts.append(hex_val)

        lines.append(f"{name}: {' '.join(hex_parts)}")

    return "\n".join(lines)


def format_gradient(
    palette: Palette, gamut: Gamut = "p3", use_color: bool = True, width: int = 60
) -> str:
    """
    Format palette as ASCII gradient bars.

    Output:
        primary (264deg):
        ░░░▒▒▒▓▓▓███████████████████████████████████▓▓▓▒▒▒░░░
    """
    lines = []

    scale_order = [
        "primary",
        "analogous-cool",
        "analogous-warm",
        "complement",
        "split-complement-cool",
        "split-complement-warm",
        "neutral",
    ]

    for name in scale_order:
        if name not in palette.scales:
            continue
        scale = palette.scales[name]

        lines.append(f"{name} ({scale.oklch_hue:.0f}deg):")

        # Build gradient
        gradient_chars = []
        for i in range(width):
            # Map position to level
            t = i / (width - 1)
            level_idx = int(t * (len(LEVELS) - 1))
            level = LEVELS[min(level_idx, len(LEVELS) - 1)]

            color = scale.colors.get(level)
            if color:
                if gamut == "p3":
                    r, g, b = rgb01_to_255(color.p3_r, color.p3_g, color.p3_b)
                else:
                    r, g, b = rgb01_to_255(color.srgb_r, color.srgb_g, color.srgb_b)

                # Choose block character based on lightness
                L = color.oklch_l
                if L > 0.8:
                    char = LIGHT_SHADE
                elif L > 0.5:
                    char = MEDIUM_SHADE
                elif L > 0.3:
                    char = DARK_SHADE
                else:
                    char = FULL_BLOCK

                if use_color:
                    gradient_chars.append(f"{rgb_fg(r, g, b)}{char}{RESET}")
                else:
                    gradient_chars.append(char)

        lines.append("".join(gradient_chars))
        lines.append("")

    return "\n".join(lines).rstrip()


def output_palette(
    palette: Palette,
    format: OutputFormat,
    gamut: Gamut = "p3",
    blocks: bool = False,
    colored_text: bool = False,
    gradient: bool = False,
    use_color: bool = True,
) -> None:
    """Output palette in requested format(s) with optional visualization."""

    # Visualization output (before format output)
    if blocks:
        print(format_blocks(palette, gamut, use_color))
        print()

    if colored_text:
        print(format_colored_text(palette, gamut, use_color))
        print()

    if gradient:
        print(format_gradient(palette, gamut, use_color))
        print()

    # Skip format output if 'none'
    if format == "none":
        return

    # Format output (existing logic)

    if format in ("palette", "all"):
        print(format_palette_block(palette, gamut))
        if format == "all":
            print()

    if format in ("tailwind", "all"):
        print(format_tailwind_config(palette))
        if format == "all":
            print()

    if format in ("json", "all"):
        print(format_json(palette))
        if format == "all":
            print()

    if format == "css":
        print(format_css(palette, use_oklch=True))

    if format == "css-hex":
        print(format_css(palette, use_oklch=False))


# ========== CLI ==========


def main() -> None:
    description = """\
PALETTE GENERATOR - OKLCH tonal scales with APCA contrast

Generate full 11-step tonal palettes (50-950) from RYB hue mixes.
Supports Display P3 and sRGB gamuts with APCA accessibility validation.
"""

    epilog = """\
EXAMPLES:
  # Basic palette with visualization
  palette.py --hue Blue:1 --blocks

  # Multi-hue with auto-adjustment and CSS output
  palette.py --hue Blue:0.6 --hue Purple:0.4 --auto-adjust --format css

  # Full JSON for programmatic use
  palette.py --hue Green:1 --format json --gamut srgb

  # Compare chroma modes
  palette.py --hue Blue:0.5 --hue Purple:0.5 --chroma-mode both

HUE NAMES:
  Red, Orange, Yellow, Green, Blue, Purple

  Format: Name:Weight (weights are normalized)
  Example: --hue Blue:0.6 --hue Purple:0.4
"""

    p = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Group: Required
    required = p.add_argument_group("REQUIRED")
    required.add_argument(
        "--hue",
        action="append",
        required=True,
        metavar="NAME:WEIGHT",
        help="RYB hue with weight (repeat 1-3 times)",
    )

    # Group: Output Format
    output = p.add_argument_group("OUTPUT FORMAT")
    output.add_argument(
        "--format",
        choices=["palette", "tailwind", "json", "css", "css-hex", "all", "none"],
        default="none",
        metavar="FORMAT",
        help="palette|tailwind|json|css|css-hex|all|none (default: none)",
    )

    # Group: Visualization
    viz = p.add_argument_group("VISUALIZATION (combinable)")
    viz.add_argument(
        "--blocks",
        action="store_true",
        help="Color block swatches",
    )
    viz.add_argument(
        "--colored-text",
        action="store_true",
        help="Hex in actual colors",
    )
    viz.add_argument(
        "--gradient",
        action="store_true",
        help="ASCII gradient per scale",
    )
    viz.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI output",
    )
    viz.add_argument(
        "--force-color",
        action="store_true",
        help="Force ANSI colors",
    )

    # Group: Color Options
    color = p.add_argument_group("COLOR OPTIONS")
    color.add_argument(
        "--gamut",
        choices=["p3", "srgb"],
        default="p3",
        help="Target gamut (default: p3)",
    )
    color.add_argument(
        "--chroma-mode",
        choices=["even", "max", "both"],
        default="even",
        help="even|max|both (default: even)",
    )
    color.add_argument(
        "--set",
        choices=["base", "adjacent", "triad", "full"],
        default="full",
        help="Palette composition (default: full)",
    )
    color.add_argument(
        "--include-complementary",
        action="store_true",
        help="Add complement hue",
    )
    color.add_argument(
        "--x",
        type=float,
        default=30.0,
        help="Offset angle (default: 30)",
    )
    color.add_argument(
        "--neutral-chroma",
        type=float,
        default=0.10,
        help="Max neutral chroma (default: 0.10 for visible tinting)",
    )

    # Group: Accessibility
    access = p.add_argument_group("ACCESSIBILITY")
    access.add_argument(
        "--auto-adjust",
        action="store_true",
        help="Auto-fix contrast failures",
    )
    access.add_argument(
        "--min-contrast",
        type=float,
        default=60.0,
        help="APCA Lc threshold (default: 60)",
    )
    access.add_argument(
        "--max-adjust",
        type=float,
        default=0.15,
        help="Max L adjustment (default: 0.15)",
    )
    access.add_argument(
        "--no-validate-apca",
        action="store_true",
        help="Skip APCA validation",
    )

    # Group: Output Control
    ctrl = p.add_argument_group("OUTPUT CONTROL")
    ctrl.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress messages",
    )

    args = p.parse_args()

    # Parse hue arguments
    if not (1 <= len(args.hue) <= 3):
        sys.exit(f"Error: Provide 1-3 --hue items (got {len(args.hue)}).")

    try:
        hue_weights = [parse_hue_arg(s) for s in args.hue]
    except ValueError as e:
        sys.exit(f"Error: {e}")

    # Normalize weights
    total_weight = sum(w for _, w in hue_weights)
    if total_weight <= 0:
        sys.exit("Error: Total weight must be positive.")
    hue_weights = [(name, w / total_weight) for name, w in hue_weights]

    # Generate palette
    if not args.quiet:
        print(
            f"Generating {args.gamut.upper()} palette ({args.chroma_mode} chroma)...",
            file=sys.stderr,
        )

    if args.chroma_mode == "both":
        # Generate both even and max
        palette_even = generate_palette(
            hue_weights=hue_weights,
            chroma_mode="even",
            gamut=args.gamut,
            palette_set=args.set,
            x_deg=args.x,
            include_complementary=args.include_complementary,
            neutral_max_chroma=args.neutral_chroma,
        )
        palette_max = generate_palette(
            hue_weights=hue_weights,
            chroma_mode="max",
            gamut=args.gamut,
            palette_set=args.set,
            x_deg=args.x,
            include_complementary=args.include_complementary,
            neutral_max_chroma=args.neutral_chroma,
        )

        # Auto-adjust if requested
        if args.auto_adjust:
            adjustments_even = auto_adjust_palette_contrast(
                palette_even, args.min_contrast, args.max_adjust
            )
            adjustments_max = auto_adjust_palette_contrast(
                palette_max, args.min_contrast, args.max_adjust
            )
            if not args.quiet:
                if adjustments_even:
                    print("# APCA Adjustments (Even)", file=sys.stderr)
                    print_adjustment_report(adjustments_even)
                if adjustments_max:
                    print("# APCA Adjustments (Max)", file=sys.stderr)
                    print_adjustment_report(adjustments_max)

        # Determine color usage
        use_color = should_use_color(args.force_color, args.no_color)

        # Output both
        print("# Even Chroma")
        output_palette(
            palette_even,
            args.format,
            args.gamut,
            blocks=args.blocks,
            colored_text=args.colored_text,
            gradient=args.gradient,
            use_color=use_color,
        )
        print("\n# Max Chroma")
        output_palette(
            palette_max,
            args.format,
            args.gamut,
            blocks=args.blocks,
            colored_text=args.colored_text,
            gradient=args.gradient,
            use_color=use_color,
        )

        if not args.no_validate_apca:
            print("\n# APCA Validation (Even)", file=sys.stderr)
            issues_even = validate_palette_contrast(palette_even, args.min_contrast)
            print_contrast_report(issues_even)
            print("# APCA Validation (Max)", file=sys.stderr)
            issues_max = validate_palette_contrast(palette_max, args.min_contrast)
            print_contrast_report(issues_max)
    else:
        palette = generate_palette(
            hue_weights=hue_weights,
            chroma_mode=args.chroma_mode,
            gamut=args.gamut,
            palette_set=args.set,
            x_deg=args.x,
            include_complementary=args.include_complementary,
            neutral_max_chroma=args.neutral_chroma,
        )

        # Auto-adjust if requested
        if args.auto_adjust:
            adjustments = auto_adjust_palette_contrast(
                palette, args.min_contrast, args.max_adjust
            )
            if not args.quiet:
                print_adjustment_report(adjustments)

        # Determine color usage
        use_color = should_use_color(args.force_color, args.no_color)

        output_palette(
            palette,
            args.format,
            args.gamut,
            blocks=args.blocks,
            colored_text=args.colored_text,
            gradient=args.gradient,
            use_color=use_color,
        )

        if not args.no_validate_apca:
            issues = validate_palette_contrast(palette, args.min_contrast)
            print_contrast_report(issues)

    if not args.quiet:
        print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
