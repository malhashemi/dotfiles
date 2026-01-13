#!/usr/bin/env python3
"""
Shared color utilities for Ripple color system.

Provides:
- Basic math utilities (clamp, deg/rad conversion, circular mean)
- RYB to RGB hue mapping
- OKLCH <-> sRGB/P3 conversions
- Display P3 gamut support
- Gamut boundary detection and max chroma search
- APCA contrast calculation
"""

import math
from typing import Dict, List, Literal, Optional, Tuple

Gamut = Literal["srgb", "p3"]

# ========== Basic Utilities ==========


def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp x to [lo, hi]."""
    return lo if x < lo else hi if x > hi else x


def deg_to_rad(d: float) -> float:
    """Convert degrees to radians."""
    return d * math.pi / 180.0


def rad_to_deg(r: float) -> float:
    """Convert radians to degrees."""
    return r * 180.0 / math.pi


def mod360(h: float) -> float:
    """Normalize angle to [0, 360)."""
    return (h % 360.0 + 360.0) % 360.0


def circular_mean_deg(hues_deg: List[float], weights: List[float]) -> float:
    """Compute weighted circular mean of angles in degrees."""
    x = 0.0
    y = 0.0
    wsum = 0.0
    for h, w in zip(hues_deg, weights):
        t = deg_to_rad(h % 360.0)
        x += w * math.cos(t)
        y += w * math.sin(t)
        wsum += w
    if wsum == 0 or (abs(x) < 1e-12 and abs(y) < 1e-12):
        return 0.0
    ang = math.atan2(y, x)
    d = (rad_to_deg(ang) + 360.0) % 360.0
    return d


# ========== Paletton RYB Color Wheel Algorithm ==========
#
# This is the exact algorithm used by Paletton.com for RYB color harmony.
# Reverse-engineered from Paletton's JavaScript source code.
#
# The RYB (Red-Yellow-Blue) artist's color wheel differs from HSV:
#   - RYB 0° = Red
#   - RYB 120° = Yellow
#   - RYB 180° = Green (NOT blue-violet!)
#   - RYB 210° = Cyan
#   - RYB 255° = Blue
#   - RYB 315° = Magenta
#
# The wheel is defined by 6 anchor points with non-linear tan/atan interpolation.
# Each anchor also has "natural" S and V values that vary around the wheel.

# ========== 6 Anchor Points ==========
# Each anchor: (name, ryb_hue, rgb_tuple, natural_s, natural_v)
# These define the pure hues at key positions on the RYB wheel.

_RYB_ANCHORS = {
    "r": {"ryb": 0, "rgb": (255, 0, 0), "s": 1.0, "v": 1.0},  # Red
    "rg": {"ryb": 120, "rgb": (255, 255, 0), "s": 1.0, "v": 1.0},  # Yellow
    "g": {"ryb": 180, "rgb": (0, 255, 0), "s": 1.0, "v": 0.8},  # Green
    "gb": {"ryb": 210, "rgb": (0, 255, 255), "s": 1.0, "v": 0.6},  # Cyan
    "b": {"ryb": 255, "rgb": (0, 0, 255), "s": 0.85, "v": 0.7},  # Blue
    "br": {"ryb": 315, "rgb": (255, 0, 255), "s": 1.0, "v": 0.65},  # Magenta
}

# ========== Segment Definitions ==========
# Each segment connects two anchors with specific interpolation formulas.
# Paletton uses tan/atan for non-linear interpolation.
#
# Key insight: Paletton alternates between two interpolation directions:
#   - "s" (forward): factor=-1 → a, factor=0 → b
#   - "i" (inverse): factor=-1 → b, factor=0 → a
#
# The segments also have different coefficient values that affect curvature.

_RYB_SEGMENTS = {
    "h": {  # 0° - 120° (red to yellow)
        "a": "r",
        "b": "rg",
        "coef": 0.5,
        "interp": "s",
        "order": lambda mx, md, mn: (mx, md, mn),  # R=max, G=mid, B=min
    },
    "c": {  # 120° - 180° (yellow to green)
        "a": "rg",
        "b": "g",
        "coef": 0.5,
        "interp": "i",
        "order": lambda mx, md, mn: (md, mx, mn),  # G=max, R=mid, B=min
    },
    "a": {  # 180° - 210° (green to cyan)
        "a": "g",
        "b": "gb",
        "coef": 0.75,
        "interp": "s",
        "order": lambda mx, md, mn: (mn, mx, md),  # G=max, B=mid, R=min
    },
    "o": {  # 210° - 255° (cyan to blue)
        "a": "gb",
        "b": "b",
        "coef": 1.33,
        "interp": "i",
        "order": lambda mx, md, mn: (mn, md, mx),  # B=max, G=mid, R=min
    },
    "n": {  # 255° - 315° (blue to magenta)
        "a": "b",
        "b": "br",
        "coef": 1.33,
        "interp": "s",
        "order": lambda mx, md, mn: (md, mn, mx),  # B=max, R=mid, G=min
    },
    "r": {  # 315° - 360° (magenta to red)
        "a": "br",
        "b": "r",
        "coef": 1.33,
        "interp": "i",
        "order": lambda mx, md, mn: (mx, mn, md),  # R=max, B=mid, G=min
    },
}


def _get_segment_for_ryb(ryb_hue: float) -> str:
    """Get segment name for a given RYB hue."""
    h = mod360(ryb_hue)
    if h < 120:
        return "h"
    elif h < 180:
        return "c"
    elif h < 210:
        return "a"
    elif h < 255:
        return "o"
    elif h < 315:
        return "n"
    else:
        return "r"


def _segment_factor(seg_name: str, ryb_hue: float) -> float:
    """
    Calculate interpolation factor for a segment.

    This matches Paletton's exact formulas for each segment.
    Returns a value that's used with _interp_s or _interp_i.
    """
    h = mod360(ryb_hue)
    coef = _RYB_SEGMENTS[seg_name]["coef"]

    if seg_name == "h":
        # 0° - 120°: f(h) = h === 0 ? -1 : tan((120-h)/120 * π/2) * 0.5
        if h == 0:
            return -1.0
        return math.tan((120.0 - h) / 120.0 * math.pi / 2.0) * coef

    elif seg_name == "c":
        # 120° - 180°: f(h) = h === 180 ? -1 : tan((h-120)/60 * π/2) * 0.5
        if h == 180:
            return -1.0
        return math.tan((h - 120.0) / 60.0 * math.pi / 2.0) * coef

    elif seg_name == "a":
        # 180° - 210°: f(h) = h === 180 ? -1 : tan((210-h)/30 * π/2) * 0.75
        if h == 180:
            return -1.0
        return math.tan((210.0 - h) / 30.0 * math.pi / 2.0) * coef

    elif seg_name == "o":
        # 210° - 255°: f(h) = h === 255 ? -1 : tan((h-210)/45 * π/2) * 1.33
        if h == 255:
            return -1.0
        return math.tan((h - 210.0) / 45.0 * math.pi / 2.0) * coef

    elif seg_name == "n":
        # 255° - 315°: f(h) = h === 255 ? -1 : tan((315-h)/60 * π/2) * 1.33
        if h == 255:
            return -1.0
        return math.tan((315.0 - h) / 60.0 * math.pi / 2.0) * coef

    else:  # "r"
        # 315° - 360°: f(h) = h === 0 ? -1 : tan((h-315)/45 * π/2) * 1.33
        if h == 0 or h == 360:
            return -1.0
        # Handle wrap: h could be 315-360 or 0
        if h >= 315:
            return math.tan((h - 315.0) / 45.0 * math.pi / 2.0) * coef
        else:
            return math.tan((h + 45.0) / 45.0 * math.pi / 2.0) * coef


def _segment_factor_inverse(seg_name: str, factor: float) -> float:
    """
    Calculate RYB hue from interpolation factor.

    Inverse of _segment_factor.
    """
    if factor == -1:
        # Return start of segment
        seg = _RYB_SEGMENTS[seg_name]
        if seg["interp"] == "s":
            return float(_RYB_ANCHORS[seg["a"]]["ryb"])
        else:
            return float(_RYB_ANCHORS[seg["b"]]["ryb"])

    coef = _RYB_SEGMENTS[seg_name]["coef"]

    if seg_name == "h":
        # Inverse: h = 120 - atan(factor/0.5) * 120 / (π/2)
        return 120.0 - math.atan(factor / coef) * 120.0 / (math.pi / 2.0)

    elif seg_name == "c":
        return 120.0 + math.atan(factor / coef) * 60.0 / (math.pi / 2.0)

    elif seg_name == "a":
        return 210.0 - math.atan(factor / coef) * 30.0 / (math.pi / 2.0)

    elif seg_name == "o":
        return 210.0 + math.atan(factor / coef) * 45.0 / (math.pi / 2.0)

    elif seg_name == "n":
        return 315.0 - math.atan(factor / coef) * 60.0 / (math.pi / 2.0)

    else:  # "r"
        h = 315.0 + math.atan(factor / coef) * 45.0 / (math.pi / 2.0)
        return mod360(h)


def _interp_s(a_val: float, b_val: float, factor: float) -> float:
    """
    Forward interpolation: factor=-1 → a, factor=0 → b
    Paletton's 's' function.
    """
    if factor == -1:
        return a_val
    return a_val + (b_val - a_val) / (1.0 + factor)


def _interp_i(a_val: float, b_val: float, factor: float) -> float:
    """
    Inverse interpolation: factor=-1 → b, factor=0 → a
    Paletton's 'i' function.
    """
    if factor == -1:
        return b_val
    return b_val + (a_val - b_val) / (1.0 + factor)


def get_base_color_for_ryb_hue(ryb_hue: float) -> Tuple[float, float]:
    """
    Get the natural (S, V) for an RYB hue.

    This is Paletton's getBaseColorByHue() function.

    Args:
        ryb_hue: RYB hue in degrees (0-360)

    Returns:
        (natural_s, natural_v) tuple - the "base" saturation and value
        for a pure color at this RYB hue position
    """
    h = mod360(ryb_hue)
    seg_name = _get_segment_for_ryb(h)
    seg = _RYB_SEGMENTS[seg_name]

    a_anchor = _RYB_ANCHORS[seg["a"]]
    b_anchor = _RYB_ANCHORS[seg["b"]]

    factor = _segment_factor(seg_name, h)

    # Interpolate S and V using segment's interpolation direction
    if seg["interp"] == "s":
        s = _interp_s(a_anchor["s"], b_anchor["s"], factor)
        v = _interp_s(a_anchor["v"], b_anchor["v"], factor)
    else:
        s = _interp_i(a_anchor["s"], b_anchor["s"], factor)
        v = _interp_i(a_anchor["v"], b_anchor["v"], factor)

    return s, v


def ryb_hsv_to_rgb(ryb_hue: float, s: float, v: float) -> Tuple[int, int, int]:
    """
    Convert RYB-HSV to RGB (0-255).

    This is Paletton's hsv2rgb() function where the H is in RYB space.

    Args:
        ryb_hue: Hue in RYB degrees (0-360)
        s: Saturation (0-1)
        v: Value/brightness (0-1)

    Returns:
        (r, g, b) tuple with values 0-255
    """
    h = mod360(ryb_hue)
    s = clamp(s, 0.0, 1.0)
    v = clamp(v, 0.0, 1.0)

    seg_name = _get_segment_for_ryb(h)
    seg = _RYB_SEGMENTS[seg_name]
    a_anchor = _RYB_ANCHORS[seg["a"]]

    factor = _segment_factor(seg_name, h)

    # Get max RGB value from anchor (always 255 for pure hues)
    a_rgb = a_anchor["rgb"]
    rgb_max = max(a_rgb)  # Always 255

    # Scale by value
    mx = rgb_max * v

    # Min is max * (1 - saturation)
    mn = mx * (1.0 - s)

    # Middle value uses interpolation based on segment direction
    if seg["interp"] == "s":
        # Forward: factor=-1 → min, higher → toward max
        if factor == -1:
            md = mn
        else:
            md = (mx + mn * factor) / (1.0 + factor)
    else:
        # Inverse: factor=-1 → max, higher → toward min
        if factor == -1:
            md = mn
        else:
            md = (mx + mn * factor) / (1.0 + factor)

    # Order RGB channels according to segment
    r, g, b = seg["order"](mx, md, mn)

    return (
        int(round(clamp(r, 0, 255))),
        int(round(clamp(g, 0, 255))),
        int(round(clamp(b, 0, 255))),
    )


def rgb_to_ryb_hsv(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """
    Convert RGB (0-255) to RYB-HSV.

    This is Paletton's rgb2hsv() function, returning H in RYB space.

    Args:
        r, g, b: RGB values 0-255 (can be float, will be rounded)

    Returns:
        (ryb_hue, s, v) tuple where ryb_hue is 0-360, s and v are 0-1
    """
    r = int(round(clamp(r, 0, 255)))
    g = int(round(clamp(g, 0, 255)))
    b = int(round(clamp(b, 0, 255)))

    # Handle grayscale
    if r == g == b:
        return (0.0, 0.0, r / 255.0)

    mx = max(r, g, b)
    mn = min(r, g, b)

    # Determine segment based on which channels are max/min
    if mx == r:
        if mn == b:
            md = g
            seg_name = "h"  # Red-Yellow segment
        else:  # mn == g
            md = b
            seg_name = "r"  # Magenta-Red segment
    elif mx == g:
        if mn == r:
            md = b
            seg_name = "a"  # Green-Cyan segment
        else:  # mn == b
            md = r
            seg_name = "c"  # Yellow-Green segment
    else:  # mx == b
        if mn == r:
            md = g
            seg_name = "o"  # Cyan-Blue segment
        else:  # mn == g
            md = r
            seg_name = "n"  # Blue-Magenta segment

    # Calculate interpolation factor from RGB values
    if md == mn:
        factor = -1.0
    else:
        factor = (mx - md) / (md - mn)

    # Get RYB hue from factor
    ryb_hue = _segment_factor_inverse(seg_name, factor)

    # Saturation and Value
    s = (mx - mn) / mx if mx > 0 else 0.0
    v = mx / 255.0

    return (ryb_hue, s, v)


def ryb_hue_to_hsv_hue(ryb_deg: float) -> float:
    """
    Convert RYB hue angle to standard HSV hue angle.

    Uses Paletton's algorithm: convert RYB to RGB, then RGB to HSV.
    """
    # Get a saturated color at this RYB hue
    r, g, b = ryb_hsv_to_rgb(ryb_deg, 1.0, 1.0)

    # Convert to standard HSV
    h, _, _ = srgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return h


def hsv_hue_to_ryb_hue(hsv_deg: float) -> float:
    """
    Convert standard HSV hue angle to RYB hue angle.

    Uses Paletton's algorithm: convert HSV to RGB, then RGB to RYB-HSV.
    """
    # Get RGB at this HSV hue
    r, g, b = hsv_to_srgb(hsv_deg, 1.0, 1.0)

    # Convert to RYB-HSV
    ryb_h, _, _ = rgb_to_ryb_hsv(
        int(round(r * 255)),
        int(round(g * 255)),
        int(round(b * 255)),
    )
    return ryb_h


# Backward compatibility aliases (RGB hue = HSV hue at S=1, V=1)
def ryb_hue_to_rgb_hue(ryb_deg: float) -> float:
    """Convert RYB hue to RGB/HSV hue. Alias for ryb_hue_to_hsv_hue()."""
    return ryb_hue_to_hsv_hue(ryb_deg)


def rgb_hue_to_ryb_hue(rgb_deg: float) -> float:
    """Convert RGB/HSV hue to RYB hue. Alias for hsv_hue_to_ryb_hue()."""
    return hsv_hue_to_ryb_hue(rgb_deg)


# ========== Gamma / Linear Conversion ==========


def srgb_to_linear(u: float) -> float:
    """Convert sRGB gamma-encoded value to linear."""
    return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4


def linear_to_srgb(u: float) -> float:
    """Convert linear value to sRGB gamma-encoded."""
    return 12.92 * u if u <= 0.0031308 else 1.055 * (u ** (1.0 / 2.4)) - 0.055


# ========== HSV Conversion (for hue mapping) ==========


def hsv_to_srgb(h_deg: float, s: float, v: float) -> Tuple[float, float, float]:
    """Convert HSV to sRGB [0,1]."""
    h = mod360(h_deg)
    s = clamp(s, 0.0, 1.0)
    v = clamp(v, 0.0, 1.0)
    c = v * s
    hp = h / 60.0
    x = c * (1.0 - abs((hp % 2.0) - 1.0))
    if 0 <= hp < 1:
        r1, g1, b1 = c, x, 0.0
    elif 1 <= hp < 2:
        r1, g1, b1 = x, c, 0.0
    elif 2 <= hp < 3:
        r1, g1, b1 = 0.0, c, x
    elif 3 <= hp < 4:
        r1, g1, b1 = 0.0, x, c
    elif 4 <= hp < 5:
        r1, g1, b1 = x, 0.0, c
    else:
        r1, g1, b1 = c, 0.0, x
    m = v - c
    return r1 + m, g1 + m, b1 + m


def srgb_to_hsv(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Convert sRGB [0,1] to HSV (H in degrees, S and V in 0-1)."""
    r = clamp(r, 0.0, 1.0)
    g = clamp(g, 0.0, 1.0)
    b = clamp(b, 0.0, 1.0)

    cmax = max(r, g, b)
    cmin = min(r, g, b)
    delta = cmax - cmin

    # Hue
    if delta < 1e-9:
        h = 0.0
    elif cmax == r:
        h = 60.0 * (((g - b) / delta) % 6)
    elif cmax == g:
        h = 60.0 * (((b - r) / delta) + 2)
    else:
        h = 60.0 * (((r - g) / delta) + 4)

    # Saturation
    s = 0.0 if cmax < 1e-9 else delta / cmax

    # Value
    v = cmax

    return mod360(h), s, v


def natural_v_for_hue(hsv_hue: float) -> float:
    """
    Return the natural V (brightness) for a given HSV hue in Paletton's system.

    Uses Paletton's 6-anchor algorithm:
    - Warm hues (red, yellow): V = 1.0
    - Green (RYB 180°): V = 0.8
    - Cyan (RYB 210°): V = 0.6
    - Blue (RYB 255°): V = 0.7
    - Magenta (RYB 315°): V = 0.65
    """
    # Convert HSV hue to RYB hue, then get natural V
    ryb_hue = hsv_hue_to_ryb_hue(hsv_hue)
    _, v = get_base_color_for_ryb_hue(ryb_hue)
    return v


def natural_v_for_ryb_hue(ryb_hue: float) -> float:
    """
    Return the natural V (brightness) for a given RYB hue.

    Uses Paletton's 6-anchor interpolation algorithm.
    """
    _, v = get_base_color_for_ryb_hue(ryb_hue)
    return v


def natural_s_for_ryb_hue(ryb_hue: float) -> float:
    """
    Return the natural S (saturation) for a given RYB hue.

    Uses Paletton's 6-anchor interpolation algorithm.

    Most hues have S=1.0, but blue (RYB 255°) has S=0.85.
    """
    s, _ = get_base_color_for_ryb_hue(ryb_hue)
    return s


def _paletton_extract_k(natural: float, actual: float) -> float:
    """
    Extract Paletton's k modifier from natural and actual values.

    From Paletton JS: t(e, t) = e === 0 ? 0 : t <= e ? t / e : (t - e) / (1 - e) + 1

    Args:
        natural: The natural S or V at this hue
        actual: The actual S or V of the color

    Returns:
        k modifier (can be > 1 if actual > natural)
    """
    if natural == 0:
        return 0.0
    if actual <= natural:
        return actual / natural
    else:
        # When actual > natural, use non-linear formula
        return (actual - natural) / (1.0 - natural) + 1.0


def _paletton_apply_k(natural: float, k: float) -> float:
    """
    Apply Paletton's k modifier to get the final S or V.

    From Paletton JS: e(e, t) = t <= 1 ? e * t : e + (1 - e) * (t - 1)

    Args:
        natural: The natural S or V at the target hue
        k: The k modifier extracted from the input color

    Returns:
        Final S or V value (clamped to 0-1)
    """
    if k <= 1.0:
        return natural * k
    else:
        # When k > 1, interpolate toward 1.0
        return natural + (1.0 - natural) * (k - 1.0)


def paletton_sv_for_ryb_hue(
    target_ryb_hue: float,
    input_s: float,
    input_v: float,
    input_ryb_hue: float,
) -> Tuple[float, float]:
    """
    Get the Paletton-style S and V for a target RYB hue.

    This is how Paletton generates harmonics: it extracts the "modifier" (kS, kV)
    from the input color using a non-linear formula, then applies it to the
    natural S/V at the target hue.

    The modifier represents how much the input color deviates from its natural
    saturation and value. When rotating to a new hue, the same deviation is applied
    to the new hue's natural values.

    From Paletton JS:
    - Extract k: k = actual <= natural ? actual/natural : (actual-natural)/(1-natural) + 1
    - Apply k:   result = k <= 1 ? natural*k : natural + (1-natural)*(k-1)

    Args:
        target_ryb_hue: Target RYB hue in degrees (the harmonic hue)
        input_s: Saturation of the input color
        input_v: Value/brightness of the input color
        input_ryb_hue: RYB hue of the input color (the base hue)

    Returns:
        (adjusted_s, adjusted_v) tuple for the target hue
    """
    # Get natural S and V at the INPUT hue
    input_nat_s, input_nat_v = get_base_color_for_ryb_hue(input_ryb_hue)

    # Get natural S and V at the TARGET hue
    target_nat_s, target_nat_v = get_base_color_for_ryb_hue(target_ryb_hue)

    # Extract k modifiers from input color (using Paletton's non-linear formula)
    k_s = _paletton_extract_k(input_nat_s, input_s)
    k_v = _paletton_extract_k(input_nat_v, input_v)

    # Apply k modifiers to target natural values
    adjusted_s = _paletton_apply_k(target_nat_s, k_s)
    adjusted_v = _paletton_apply_k(target_nat_v, k_v)

    # Clamp to valid range
    adjusted_s = clamp(adjusted_s, 0.0, 1.0)
    adjusted_v = clamp(adjusted_v, 0.0, 1.0)

    return adjusted_s, adjusted_v


# ========== Color Space Conversions ==========


def srgb_to_oklab(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Convert sRGB [0,1] to OKLab."""
    R = srgb_to_linear(clamp(r, 0.0, 1.0))
    G = srgb_to_linear(clamp(g, 0.0, 1.0))
    B = srgb_to_linear(clamp(b, 0.0, 1.0))

    l = 0.4122214708 * R + 0.5363325363 * G + 0.0514459929 * B
    m = 0.2119034982 * R + 0.6806995451 * G + 0.1073969566 * B
    s = 0.0883024619 * R + 0.2817188376 * G + 0.6299797005 * B

    l_ = l ** (1.0 / 3.0) if l >= 0 else -((-l) ** (1.0 / 3.0))
    m_ = m ** (1.0 / 3.0) if m >= 0 else -((-m) ** (1.0 / 3.0))
    s_ = s ** (1.0 / 3.0) if s >= 0 else -((-s) ** (1.0 / 3.0))

    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b2 = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, a, b2


def oklch_to_oklab(L: float, C: float, h_deg: float) -> Tuple[float, float, float]:
    """Convert OKLCH to OKLab."""
    h = deg_to_rad(h_deg)
    a = C * math.cos(h)
    b = C * math.sin(h)
    return L, a, b


def oklab_to_linear_srgb(L: float, a: float, b: float) -> Tuple[float, float, float]:
    """Convert OKLab to linear sRGB."""
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l3 = l_**3
    m3 = m_**3
    s3 = s_**3

    r = +4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3
    g = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3
    b2 = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3
    return r, g, b2


def oklch_to_linear_srgb(
    L: float, C: float, h_deg: float
) -> Tuple[float, float, float]:
    """Convert OKLCH to linear sRGB."""
    _, a, b = oklch_to_oklab(L, C, h_deg)
    return oklab_to_linear_srgb(L, a, b)


# ========== Display P3 Support ==========

# P3 to XYZ D65 matrix (from CSS Color 4 spec)
_P3_TO_XYZ = [
    [0.4865709486, 0.2656676932, 0.1982172852],
    [0.2289745641, 0.6917385218, 0.0792869141],
    [0.0000000000, 0.0451133819, 1.0439443689],
]

# XYZ D65 to P3 matrix (inverse)
_XYZ_TO_P3 = [
    [2.4934969119, -0.9313836179, -0.4027107845],
    [-0.8294889696, 1.7626640603, 0.0236246858],
    [0.0358458302, -0.0761723893, 0.9568845240],
]

# sRGB to XYZ D65 matrix
_SRGB_TO_XYZ = [
    [0.4124564, 0.3575761, 0.1804375],
    [0.2126729, 0.7151522, 0.0721750],
    [0.0193339, 0.1191920, 0.9503041],
]

# XYZ D65 to sRGB matrix
_XYZ_TO_SRGB = [
    [3.2404542, -1.5371385, -0.4985314],
    [-0.9692660, 1.8760108, 0.0415560],
    [0.0556434, -0.2040259, 1.0572252],
]


def _matmul3(
    matrix: List[List[float]], vec: Tuple[float, float, float]
) -> Tuple[float, float, float]:
    """Multiply 3x3 matrix by 3-vector."""
    return (
        matrix[0][0] * vec[0] + matrix[0][1] * vec[1] + matrix[0][2] * vec[2],
        matrix[1][0] * vec[0] + matrix[1][1] * vec[1] + matrix[1][2] * vec[2],
        matrix[2][0] * vec[0] + matrix[2][1] * vec[1] + matrix[2][2] * vec[2],
    )


def linear_srgb_to_xyz(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Convert linear sRGB to XYZ D65."""
    return _matmul3(_SRGB_TO_XYZ, (r, g, b))


def xyz_to_linear_srgb(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Convert XYZ D65 to linear sRGB."""
    return _matmul3(_XYZ_TO_SRGB, (x, y, z))


def linear_p3_to_xyz(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Convert linear Display P3 to XYZ D65."""
    return _matmul3(_P3_TO_XYZ, (r, g, b))


def xyz_to_linear_p3(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """Convert XYZ D65 to linear Display P3."""
    return _matmul3(_XYZ_TO_P3, (x, y, z))


def oklab_to_xyz(L: float, a: float, b: float) -> Tuple[float, float, float]:
    """Convert OKLab to XYZ D65."""
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l = l_**3
    m = m_**3
    s = s_**3

    # LMS to XYZ (using OKLab's specific matrix)
    x = 1.2270138511 * l - 0.5577999807 * m + 0.2812561490 * s
    y = -0.0405801784 * l + 1.1122568696 * m - 0.0716766787 * s
    z = -0.0763812845 * l - 0.4214819784 * m + 1.5861632204 * s
    return x, y, z


def oklch_to_linear_p3(L: float, C: float, h_deg: float) -> Tuple[float, float, float]:
    """Convert OKLCH to linear Display P3."""
    _, a, b = oklch_to_oklab(L, C, h_deg)
    x, y, z = oklab_to_xyz(L, a, b)
    return xyz_to_linear_p3(x, y, z)


def oklch_in_p3_gamut(L: float, C: float, h_deg: float, eps: float = 1e-6) -> bool:
    """Check if OKLCH color is within Display P3 gamut."""
    r, g, b = oklch_to_linear_p3(L, C, h_deg)
    return linear_rgb_in_gamut(r, g, b, eps)


def oklch_to_p3(L: float, C: float, h_deg: float) -> Tuple[float, float, float, bool]:
    """
    Convert OKLCH to Display P3 [0,1], returning (r, g, b, in_gamut).

    Uses same gamma curve as sRGB (2.4 with linear segment).
    """
    r_lin, g_lin, b_lin = oklch_to_linear_p3(L, C, h_deg)
    in_gamut = linear_rgb_in_gamut(r_lin, g_lin, b_lin, eps=1e-6)

    # Clamp and gamma encode (P3 uses sRGB transfer function)
    r_lin = clamp(r_lin, -1e-6, 1.0 + 1e-6)
    g_lin = clamp(g_lin, -1e-6, 1.0 + 1e-6)
    b_lin = clamp(b_lin, -1e-6, 1.0 + 1e-6)

    r = clamp(linear_to_srgb(r_lin), 0.0, 1.0)
    g = clamp(linear_to_srgb(g_lin), 0.0, 1.0)
    b = clamp(linear_to_srgb(b_lin), 0.0, 1.0)
    return r, g, b, in_gamut


def p3_to_srgb_fallback(
    r_p3: float, g_p3: float, b_p3: float
) -> Tuple[float, float, float, bool]:
    """
    Convert P3 color to sRGB, with gamut mapping if needed.

    Returns (r, g, b, was_clipped).
    If the P3 color is outside sRGB, reduces chroma to fit.
    """
    # Linearize P3
    r_lin = srgb_to_linear(r_p3)
    g_lin = srgb_to_linear(g_p3)
    b_lin = srgb_to_linear(b_p3)

    # P3 -> XYZ -> sRGB
    x, y, z = linear_p3_to_xyz(r_lin, g_lin, b_lin)
    sr, sg, sb = xyz_to_linear_srgb(x, y, z)

    # Check if in sRGB gamut
    in_gamut = linear_rgb_in_gamut(sr, sg, sb, eps=1e-6)

    # Clamp and gamma encode
    sr = clamp(linear_to_srgb(clamp(sr, 0.0, 1.0)), 0.0, 1.0)
    sg = clamp(linear_to_srgb(clamp(sg, 0.0, 1.0)), 0.0, 1.0)
    sb = clamp(linear_to_srgb(clamp(sb, 0.0, 1.0)), 0.0, 1.0)

    return sr, sg, sb, not in_gamut


def css_p3_string(r: float, g: float, b: float) -> str:
    """Format as CSS color(display-p3 r g b) string."""
    return f"color(display-p3 {r:.4f} {g:.4f} {b:.4f})"


# ========== Gamut Checking ==========


def linear_rgb_in_gamut(r: float, g: float, b: float, eps: float = 1e-9) -> bool:
    """Check if linear RGB values are in [0, 1] gamut."""
    return -eps <= r <= 1.0 + eps and -eps <= g <= 1.0 + eps and -eps <= b <= 1.0 + eps


def oklch_to_srgb(L: float, C: float, h_deg: float) -> Tuple[float, float, float, bool]:
    """
    Convert OKLCH to sRGB [0,1], returning (r, g, b, in_gamut).

    Does NOT clip - caller should handle out-of-gamut colors.
    """
    r_lin, g_lin, b_lin = oklch_to_linear_srgb(L, C, h_deg)
    in_gamut = linear_rgb_in_gamut(r_lin, g_lin, b_lin, eps=1e-6)

    # Tiny numerical safety clamp before gamma
    r_lin = clamp(r_lin, -1e-6, 1.0 + 1e-6)
    g_lin = clamp(g_lin, -1e-6, 1.0 + 1e-6)
    b_lin = clamp(b_lin, -1e-6, 1.0 + 1e-6)

    r = clamp(linear_to_srgb(r_lin), 0.0, 1.0)
    g = clamp(linear_to_srgb(g_lin), 0.0, 1.0)
    b = clamp(linear_to_srgb(b_lin), 0.0, 1.0)
    return r, g, b, in_gamut


# ========== Hex Conversion ==========


def hex_from_rgb01(r: float, g: float, b: float) -> str:
    """Convert RGB [0,1] to hex string."""
    ri = int(round(clamp(r, 0.0, 1.0) * 255.0))
    gi = int(round(clamp(g, 0.0, 1.0) * 255.0))
    bi = int(round(clamp(b, 0.0, 1.0) * 255.0))
    return "#{:02X}{:02X}{:02X}".format(ri, gi, bi)


def rgb01_from_hex(hex_str: str) -> Tuple[float, float, float]:
    """Convert hex string to RGB [0,1]."""
    hex_str = hex_str.lstrip("#")
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return r, g, b


def srgb_to_oklch(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """
    Convert sRGB [0,1] to OKLCH (L, C, H).

    Args:
        r, g, b: sRGB values in 0-1 range

    Returns:
        (L, C, H) where L is 0-1, C is 0-0.37, H is 0-360 degrees
    """
    L, a, b2 = srgb_to_oklab(r, g, b)
    C = math.sqrt(a * a + b2 * b2)
    H = (rad_to_deg(math.atan2(b2, a)) + 360.0) % 360.0
    return L, C, H


def hex_to_oklch(hex_str: str) -> Tuple[float, float, float]:
    """
    Convert hex color string to OKLCH (L, C, H).

    Args:
        hex_str: Hex color like "#FF5500" or "FF5500"

    Returns:
        (L, C, H) where L is 0-1, C is 0-0.37, H is 0-360 degrees
    """
    r, g, b = rgb01_from_hex(hex_str)
    return srgb_to_oklch(r, g, b)


# ========== RGB Hue to OKLCH Hue ==========


def rgb_hue_to_oklch_hue_deg(rgb_h_deg: float) -> float:
    """Convert RGB hue angle to OKLCH hue angle."""
    r, g, b = hsv_to_srgb(rgb_h_deg, 1.0, 1.0)
    _, a, b2 = srgb_to_oklab(r, g, b)
    ang = (rad_to_deg(math.atan2(b2, a)) + 360.0) % 360.0
    return ang


def oklch_hue_to_rgb_hue_deg(oklch_h_deg: float) -> float:
    """
    Convert OKLCH hue angle to approximate RGB hue angle.

    Uses binary search to find the RGB hue that maps to the target OKLCH hue.
    """
    target = mod360(oklch_h_deg)

    # Binary search for the RGB hue
    low, high = 0.0, 360.0
    for _ in range(20):  # 20 iterations gives ~0.0003° precision
        mid = (low + high) / 2
        oklch_at_mid = rgb_hue_to_oklch_hue_deg(mid)

        # Handle wrap-around at 360°
        diff = (oklch_at_mid - target + 540) % 360 - 180

        if abs(diff) < 0.01:
            return mid
        elif diff > 0:
            high = mid
        else:
            low = mid

    return (low + high) / 2


def oklch_hue_to_ryb_hue(oklch_h_deg: float) -> float:
    """Convert OKLCH hue to RYB hue (for artistic color harmony)."""
    rgb_hue = oklch_hue_to_rgb_hue_deg(oklch_h_deg)
    return rgb_hue_to_ryb_hue(rgb_hue)


def ryb_hue_to_oklch_hue(ryb_h_deg: float) -> float:
    """Convert RYB hue to OKLCH hue."""
    rgb_hue = ryb_hue_to_rgb_hue(ryb_h_deg)
    return rgb_hue_to_oklch_hue_deg(rgb_hue)


# ========== Max Chroma Search ==========


def cmax_for_L_h(
    L: float, h_deg: float, gamut: Gamut = "srgb", hi_start: float = 0.5
) -> float:
    """
    Find maximum chroma for given L and hue that stays in gamut.

    Uses binary search with expanding upper bound.

    Args:
        L: Lightness value (0-1)
        h_deg: Hue angle in degrees
        gamut: Target gamut ("srgb" or "p3")
        hi_start: Initial upper bound for binary search

    Returns:
        Maximum chroma value that stays in gamut
    """
    lo, hi = 0.0, hi_start

    # Select gamut check function based on target gamut
    if gamut == "p3":
        in_gamut_fn = lambda L, C, h: oklch_in_p3_gamut(L, C, h)
    else:
        in_gamut_fn = lambda L, C, h: linear_rgb_in_gamut(
            *oklch_to_linear_srgb(L, C, h)
        )

    # Grow hi until out of gamut
    for _ in range(8):
        if not in_gamut_fn(L, hi, h_deg):
            break
        hi *= 1.5
        if hi > 1.2:
            hi = 1.2
            break

    # Binary search for boundary
    for _ in range(28):
        mid = 0.5 * (lo + hi)
        if in_gamut_fn(L, mid, h_deg):
            lo = mid
        else:
            hi = mid

    return lo


# ========== APCA Contrast Calculation ==========
# Based on APCA-W3 version 0.98G-4g
# Reference: https://github.com/Myndex/SAPC-APCA

# APCA Constants
_APCA_MAIN_TRC = 2.4

# sRGB coefficients for APCA (Rec. 709 primaries)
_APCA_S_RCO = 0.2126729
_APCA_S_GCO = 0.7151522
_APCA_S_BCO = 0.0721750

# Display P3 coefficients for APCA (wider gamut primaries)
# Derived from CIE 1931 2° standard observer for P3 primaries
# Reference: https://github.com/Myndex/apca-w3
_APCA_P3_RCO = 0.2289829594805780
_APCA_P3_GCO = 0.6917492625852380
_APCA_P3_BCO = 0.0792677779341829

# Polarity-dependent exponents
_APCA_NORM_BG = 0.56
_APCA_NORM_TXT = 0.57
_APCA_REV_BG = 0.65
_APCA_REV_TXT = 0.62

# Black level soft clamp
_APCA_BLK_THRS = 0.022
_APCA_BLK_CLMP = 1.414

# Scaling and offsets
_APCA_SCALE_BOW = 1.14
_APCA_SCALE_WOB = 1.14
_APCA_LO_CLIP = 0.001
_APCA_LO_OFFSET = 0.027
_APCA_LO_THRESHOLD = 0.035991
_APCA_LO_FACTOR = 27.7847239587675
_APCA_DELTA_Y_MIN = 0.0005


def srgb_to_y_apca(r: int, g: int, b: int) -> float:
    """
    Convert sRGB (0-255) to APCA luminance Y.

    Uses APCA's specific gamma and coefficients.
    """

    def simple_exp(chan: int) -> float:
        return (chan / 255.0) ** _APCA_MAIN_TRC

    return (
        _APCA_S_RCO * simple_exp(r)
        + _APCA_S_GCO * simple_exp(g)
        + _APCA_S_BCO * simple_exp(b)
    )


def p3_to_y_apca(r: float, g: float, b: float) -> float:
    """
    Convert Display P3 (0.0-1.0) to APCA luminance Y.

    Uses P3-specific coefficients derived from CIE 1931 2° standard observer.
    Note: P3 uses the same gamma (2.4) as sRGB for APCA purposes.
    """
    return (
        _APCA_P3_RCO * (r**_APCA_MAIN_TRC)
        + _APCA_P3_GCO * (g**_APCA_MAIN_TRC)
        + _APCA_P3_BCO * (b**_APCA_MAIN_TRC)
    )


def apca_contrast(txt_y: float, bg_y: float) -> float:
    """
    Calculate APCA contrast from luminance values.

    IMPORTANT: Do NOT swap text and background - polarity matters!

    Returns Lc (lightness contrast) from ~-108 to ~+106.
    - Positive = dark text on light background
    - Negative = light text on dark background
    """
    # Black soft clamp
    if txt_y < _APCA_BLK_THRS:
        txt_y += math.pow(_APCA_BLK_THRS - txt_y, _APCA_BLK_CLMP)
    if bg_y < _APCA_BLK_THRS:
        bg_y += math.pow(_APCA_BLK_THRS - bg_y, _APCA_BLK_CLMP)

    # Early exit for extremely low delta Y
    if abs(bg_y - txt_y) < _APCA_DELTA_Y_MIN:
        return 0.0

    # Calculate SAPC (raw contrast)
    if bg_y > txt_y:
        # Normal polarity: dark text on light background (BoW)
        sapc = (
            math.pow(bg_y, _APCA_NORM_BG) - math.pow(txt_y, _APCA_NORM_TXT)
        ) * _APCA_SCALE_BOW

        # Low contrast smoothing
        if sapc < _APCA_LO_CLIP:
            return 0.0
        elif sapc < _APCA_LO_THRESHOLD:
            output = sapc - sapc * _APCA_LO_FACTOR * _APCA_LO_OFFSET
        else:
            output = sapc - _APCA_LO_OFFSET
    else:
        # Reverse polarity: light text on dark background (WoB)
        sapc = (
            math.pow(bg_y, _APCA_REV_BG) - math.pow(txt_y, _APCA_REV_TXT)
        ) * _APCA_SCALE_WOB

        # Low contrast smoothing (returns negative)
        if sapc > -_APCA_LO_CLIP:
            return 0.0
        elif sapc > -_APCA_LO_THRESHOLD:
            output = sapc - sapc * _APCA_LO_FACTOR * _APCA_LO_OFFSET
        else:
            output = sapc + _APCA_LO_OFFSET

    return output * 100.0


def calc_apca(
    text_rgb: Tuple[int, int, int],
    bg_rgb: Tuple[int, int, int],
) -> float:
    """
    Calculate APCA Lc contrast between text and background.

    Args:
        text_rgb: (r, g, b) tuple with values 0-255
        bg_rgb: (r, g, b) tuple with values 0-255

    Returns:
        Lc value from ~-108 to ~+106
        Use abs(Lc) for threshold comparisons
    """
    txt_y = srgb_to_y_apca(*text_rgb)
    bg_y = srgb_to_y_apca(*bg_rgb)
    return apca_contrast(txt_y, bg_y)


def calc_apca_from_rgb01(
    text_rgb: Tuple[float, float, float],
    bg_rgb: Tuple[float, float, float],
) -> float:
    """
    Calculate APCA Lc contrast from RGB [0,1] values.

    Convenience wrapper that converts to 0-255 range.
    """
    text_255 = (
        int(round(text_rgb[0] * 255)),
        int(round(text_rgb[1] * 255)),
        int(round(text_rgb[2] * 255)),
    )
    bg_255 = (
        int(round(bg_rgb[0] * 255)),
        int(round(bg_rgb[1] * 255)),
        int(round(bg_rgb[2] * 255)),
    )
    return calc_apca(text_255, bg_255)


def calc_apca_p3(
    text_rgb: Tuple[float, float, float],
    bg_rgb: Tuple[float, float, float],
) -> float:
    """
    Calculate APCA Lc contrast for Display P3 colors.

    Args:
        text_rgb: P3 color as (r, g, b) tuple with values 0.0-1.0
        bg_rgb: P3 color as (r, g, b) tuple with values 0.0-1.0

    Returns:
        Lc value from ~-108 to ~+106
        Use abs(Lc) for threshold comparisons

    Note: Both colors must be in P3 color space. Do not mix P3 and sRGB.
    """
    txt_y = p3_to_y_apca(*text_rgb)
    bg_y = p3_to_y_apca(*bg_rgb)
    return apca_contrast(txt_y, bg_y)


def calc_apca_for_gamut(
    text_rgb: Tuple[float, float, float],
    bg_rgb: Tuple[float, float, float],
    gamut: Gamut,
) -> float:
    """
    Calculate APCA contrast using the appropriate coefficients for the gamut.

    Args:
        text_rgb: Color as (r, g, b) tuple with values 0.0-1.0
        bg_rgb: Background as (r, g, b) tuple with values 0.0-1.0
        gamut: "srgb" or "p3" - determines which coefficients to use

    Returns:
        Lc value from ~-108 to ~+106

    This function selects the correct APCA calculation based on gamut:
    - For sRGB: Uses Rec. 709 luminance coefficients
    - For P3: Uses P3 primaries luminance coefficients
    """
    if gamut == "p3":
        return calc_apca_p3(text_rgb, bg_rgb)
    else:
        return calc_apca_from_rgb01(text_rgb, bg_rgb)


def auto_adjust_for_contrast(
    L: float,
    C: float,
    H: float,
    bg_rgb: Tuple[float, float, float],
    min_lc: float,
    direction: Literal["lighter", "darker"],
    gamut: Gamut = "srgb",
    max_delta_l: float = 0.15,
) -> Tuple[float, float, float, float, bool]:
    """
    Adjust L to achieve target APCA contrast via binary search.

    Args:
        L, C, H: Original OKLCH values
        bg_rgb: Background color as RGB 0-1 (must match gamut parameter)
        min_lc: Minimum absolute Lc required
        direction: "lighter" or "darker"
        gamut: Target gamut - determines both chroma reduction and APCA coefficients
        max_delta_l: Maximum allowed L change (default 0.15)

    Returns:
        (L_new, C_new, H, achieved_lc, success)
        - success is False if target couldn't be met within limits

    Note: When gamut="p3", bg_rgb should be P3 values and APCA uses P3 coefficients.
          When gamut="srgb", bg_rgb should be sRGB values and APCA uses sRGB coefficients.
    """
    L_original = L

    # Set search bounds based on direction
    if direction == "lighter":
        L_low, L_high = L, min(L + max_delta_l, 0.99)
    else:
        L_low, L_high = max(L - max_delta_l, 0.01), L

    best_L = L
    best_C = C
    best_lc = 0.0

    # Binary search for 20 iterations (~10^-6 precision)
    for _ in range(20):
        L_mid = (L_low + L_high) / 2

        # Check if in gamut, reduce C if needed
        C_test = C
        if gamut == "p3":
            if not oklch_in_p3_gamut(L_mid, C_test, H):
                C_test = cmax_for_L_h(L_mid, H, "p3") * 0.98
        else:
            if not linear_rgb_in_gamut(*oklch_to_linear_srgb(L_mid, C_test, H)):
                C_test = cmax_for_L_h(L_mid, H, "srgb") * 0.98

        # Convert to RGB and calculate APCA using gamut-appropriate method
        if gamut == "p3":
            r, g, b, _ = oklch_to_p3(L_mid, C_test, H)
            lc = abs(calc_apca_p3((r, g, b), bg_rgb))
        else:
            r, g, b, _ = oklch_to_srgb(L_mid, C_test, H)
            lc = abs(calc_apca_from_rgb01((r, g, b), bg_rgb))

        # Track best result
        if lc >= min_lc:
            best_L = L_mid
            best_C = C_test
            best_lc = lc
            # Try to stay closer to original L
            if direction == "lighter":
                L_high = L_mid
            else:
                L_low = L_mid
        else:
            # Need more contrast, move away from background
            if direction == "lighter":
                L_low = L_mid
            else:
                L_high = L_mid

    success = best_lc >= min_lc
    return best_L, best_C, H, best_lc, success


# APCA Thresholds (Bronze Simple Mode)
APCA_THRESHOLD_BODY_PREFERRED = 90.0  # Body text, min 14px/400
APCA_THRESHOLD_BODY_MINIMUM = 75.0  # Body text, min 18px/400 or 14px/700
APCA_THRESHOLD_LARGE_TEXT = 60.0  # Non-body readable, min 24px/400
APCA_THRESHOLD_HEADLINES = 45.0  # Large text, headlines, min 36px/400
APCA_THRESHOLD_MINIMUM = 30.0  # Absolute minimum for any text


# ========== RYB Hue Anchors ==========
#
# Standard RYB color wheel anchor points (in degrees).
# Used for hue mixing and parsing user input like "--hue Blue:0.5".

RYB_ANCHOR_DEG = {
    "Red": 0.0,
    "Orange": 60.0,
    "Yellow": 120.0,
    "Green": 180.0,
    "Blue": 240.0,
    "Purple": 300.0,
}


def normalize_hue_name(name: str) -> Optional[str]:
    """
    Normalize hue name to canonical form (case-insensitive).

    Args:
        name: Input hue name like "blue", "BLUE", or "Blue"

    Returns:
        Canonical name ("Blue") or None if not recognized
    """
    key = name.strip().lower()
    for k in RYB_ANCHOR_DEG:
        if k.lower() == key:
            return k
    return None


def parse_hue_arg(s: str) -> Tuple[str, float]:
    """
    Parse hue argument as 'Name:Weight'.

    Args:
        s: String like "Blue:0.5" or "Purple:0.3"

    Returns:
        (canonical_name, weight) tuple

    Raises:
        ValueError: If format is invalid or hue name not recognized
    """
    s = s.strip()
    if ":" not in s:
        raise ValueError(f"Invalid --hue '{s}'. Use 'Name:Weight', e.g., 'Blue:0.5'.")

    name_part, weight_part = s.split(":", 1)
    name = normalize_hue_name(name_part)
    if not name:
        raise ValueError(
            f"Unknown hue '{name_part}'. "
            f"Allowed: Red, Orange, Yellow, Green, Blue, Purple."
        )

    try:
        weight = float(weight_part.strip())
    except Exception as e:
        raise ValueError(f"Invalid weight in '--hue {s}': {e}")

    return name, weight
