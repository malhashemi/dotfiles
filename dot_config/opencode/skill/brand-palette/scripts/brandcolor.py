#!/usr/bin/env python3
# scripts/brandcolor.py
#
# Compute a primary brand color (and a chosen harmonic set) from RYB hue mix,
# chroma intent, and tone intent using OKLCH. Chroma is selected to keep L and
# C constant across all output hues without clipping, based on either:
# - the specific hues in your selected set (harmonics scope, more vivid), or
# - the entire 360° hue wheel at the chosen tone (global scope, most safe).
#
# Examples:
#   uv run scripts/brandcolor.py \
#     --hue Blue:0.55 --hue Purple:0.3 --hue Green:0.15 \
#     --chroma 62 --tone 52 \
#     --set full --x 30 --include-complementary \
#     --chroma-scope harmonics --plain
#
#   uv run scripts/brandcolor.py \
#     --hue Blue:1 --chroma 80 --tone 55 \
#     --set base --include-complementary --chroma-scope global

import argparse
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# Import shared utilities from color_utils
from color_utils import (
    clamp,
    mod360,
    circular_mean_deg,
    ryb_hue_to_rgb_hue,
    rgb_hue_to_oklch_hue_deg,
    oklch_to_srgb,
    oklch_to_p3,
    hex_from_rgb01,
    cmax_for_L_h,
    linear_rgb_in_gamut,
    oklch_to_linear_srgb,
    # HSV conversions for base color generation
    rgb01_from_hex,
    # sRGB to OKLCH conversion (for extracting OKLCH from Paletton outputs)
    srgb_to_oklch,
    # Paletton RYB-HSV system (exact algorithm)
    rgb_to_ryb_hsv,
    ryb_hsv_to_rgb,
    paletton_sv_for_ryb_hue,
    # Shared hue parsing utilities
    RYB_ANCHOR_DEG,
    normalize_hue_name,
    parse_hue_arg,
)


# ---------- Utilities ----------


def log(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg, file=sys.stderr, flush=True)


# ---------- Palette construction ----------


def build_ryb_palette(
    H_base_ryb: float, mode: str, x_deg: float, include_comp: bool
) -> List[Tuple[str, float]]:
    """
    Build ordered list of (label, RYB hue deg) including:
    - base always
    - optionally adjacent_left/right (±X)
    - optionally complementary (+180)
    - optionally triad_left/right (180±X)
    Dedupe by hue to avoid repeats.
    """
    parts: List[Tuple[str, float]] = [("base", mod360(H_base_ryb))]
    if mode in ("adjacent", "full"):
        parts.append(("adjacent_left", mod360(H_base_ryb - x_deg)))
        parts.append(("adjacent_right", mod360(H_base_ryb + x_deg)))
    if include_comp:
        parts.append(("complementary", mod360(H_base_ryb + 180.0)))
    if mode in ("triad", "full"):
        parts.append(("triad_left", mod360(H_base_ryb + 180.0 - x_deg)))
        parts.append(("triad_right", mod360(H_base_ryb + 180.0 + x_deg)))

    # Dedupe while preserving first occurrence
    out: List[Tuple[str, float]] = []
    seen: List[float] = []
    for lab, h in parts:
        if not any(abs(((h - s + 540.0) % 360.0) - 180.0) < 1e-7 for s in seen):
            out.append((lab, h))
            seen.append(h)
    return out


# ---------- Data Structures ----------


@dataclass
class BrandColorResult:
    """Complete brand color computation result."""

    primary_ryb_hue: float  # Primary hue in RYB degrees
    oklch_hues: Dict[str, float] = field(default_factory=dict)  # {label: oklch_hue_deg}
    L: float = 0.0  # Chosen lightness (0-1)
    C: float = 0.0  # Chosen chroma (0-0.37)
    hex_codes: Dict[str, str] = field(default_factory=dict)  # {label: srgb_hex_code}
    hex_codes_p3: Dict[str, str] = field(default_factory=dict)  # {label: p3_hex_code}
    srgb_values: Dict[str, Tuple[float, float, float]] = field(
        default_factory=dict
    )  # {label: (r,g,b)}
    p3_values: Dict[str, Tuple[float, float, float]] = field(
        default_factory=dict
    )  # {label: (r,g,b)}
    labels: List[str] = field(default_factory=list)  # Ordered list of labels


# ---------- Core Computation ----------


def compute_brand_colors(
    hue_weights: List[Tuple[str, float]],
    chroma_intent: int = 50,
    tone_intent: int = 50,
    palette_set: str = "full",
    x_deg: float = 30.0,
    include_complementary: bool = False,
    chroma_scope: str = "harmonics",
    chroma_margin: float = 0.98,
    global_sample_deg: int = 2,
) -> BrandColorResult:
    """
    Compute brand colors programmatically.

    Args:
        hue_weights: List of (hue_name, weight) tuples. Names must be one of
                     Red, Orange, Yellow, Green, Blue, Purple.
        chroma_intent: Chroma intent 0-100 (0=gray, 100=max vivid)
        tone_intent: Tone/Lightness intent 0-100 (0=near-black, 100=near-white)
        palette_set: "base", "adjacent", "triad", or "full"
        x_deg: Angle for adjacent/triad offsets
        include_complementary: Include complement hue
        chroma_scope: "harmonics" or "global"
        chroma_margin: Safety margin multiplier for Cmax
        global_sample_deg: Sampling step for global chroma scope

    Returns:
        BrandColorResult with computed colors
    """
    # Resolve names to degrees and normalize weights
    hues_ryb: List[float] = []
    weights: List[float] = []
    for name, w in hue_weights:
        normalized = normalize_hue_name(name)
        if not normalized:
            raise ValueError(f"Unknown hue name '{name}'")
        hues_ryb.append(RYB_ANCHOR_DEG[normalized])
        weights.append(float(w))

    # Normalize weights
    wsum = sum(max(0.0, w) for w in weights)
    if wsum <= 0:
        raise ValueError("All weights are zero or negative.")
    weights = [w / wsum for w in weights]

    # Step 1: Weighted primary on RYB
    H_ryb = circular_mean_deg(hues_ryb, weights)

    # Step 2: Build requested RYB palette
    ryb_palette = build_ryb_palette(H_ryb, palette_set, x_deg, include_complementary)

    # Step 3: Map to RGB hue then to OKLCH hue
    oklch_hues_list = []
    for _, h_ryb in ryb_palette:
        h_rgb = ryb_hue_to_rgb_hue(h_ryb)
        h_oklch = rgb_hue_to_oklch_hue_deg(h_rgb)
        oklch_hues_list.append(h_oklch)

    # Step 4: Map intents to OKLCH L and C (select C safely)
    L = clamp(tone_intent / 100.0, 0.0, 1.0)
    C_cap = 0.37  # absolute cap per spec
    C_user = clamp(chroma_intent / 100.0, 0.0, 1.0) * C_cap

    # Determine hues to evaluate for Cmax based on scope
    if chroma_scope == "harmonics":
        eval_hues = oklch_hues_list[:]
    else:
        step = max(1, int(global_sample_deg))
        eval_hues = [float(h) for h in range(0, 360, step)]

    # Compute per-hue Cmax and choose common safe chroma
    cmax_list = [(h, cmax_for_L_h(L, h)) for h in eval_hues]
    min_cmax = min(c for (_, c) in cmax_list) if cmax_list else 0.0
    C_safe = chroma_margin * min_cmax
    C_final = max(0.0, min(C_user, C_safe))

    # Step 5: Build colors with constant L and C_final, convert to sRGB
    srgb_list: List[Tuple[float, float, float]] = []
    any_oog = False
    for h in oklch_hues_list:
        r, g, b, in_gamut = oklch_to_srgb(L, C_final, h)
        srgb_list.append((r, g, b))
        if not in_gamut:
            any_oog = True

    # Safety: if any was unexpectedly OOG, reduce C slightly and retry once
    if any_oog:
        C_final *= 0.9995
        srgb_list = []
        for h in oklch_hues_list:
            r, g, b, _ = oklch_to_srgb(L, C_final, h)
            srgb_list.append((r, g, b))

    # Step 6: Also compute P3 values
    p3_list: List[Tuple[float, float, float]] = []
    for h in oklch_hues_list:
        r, g, b, _ = oklch_to_p3(L, C_final, h)
        p3_list.append((r, g, b))

    # Build result
    labels = [lab for lab, _ in ryb_palette]
    hex_codes = {
        lab: hex_from_rgb01(r, g, b)
        for (lab, _), (r, g, b) in zip(ryb_palette, srgb_list)
    }
    hex_codes_p3 = {
        lab: hex_from_rgb01(r, g, b)
        for (lab, _), (r, g, b) in zip(ryb_palette, p3_list)
    }
    oklch_hues_dict = {lab: h for (lab, _), h in zip(ryb_palette, oklch_hues_list)}
    srgb_values = {lab: rgb for (lab, _), rgb in zip(ryb_palette, srgb_list)}
    p3_values = {lab: rgb for (lab, _), rgb in zip(ryb_palette, p3_list)}

    return BrandColorResult(
        primary_ryb_hue=H_ryb,
        oklch_hues=oklch_hues_dict,
        L=L,
        C=C_final,
        hex_codes=hex_codes,
        hex_codes_p3=hex_codes_p3,
        srgb_values=srgb_values,
        p3_values=p3_values,
        labels=labels,
    )


def brand_color_from_hex(
    hex_color: str,
    palette_set: str = "full",
    x_deg: float = 30.0,
    include_complementary: bool = False,
) -> BrandColorResult:
    """
    Create a BrandColorResult from an existing hex color.

    Uses Paletton's exact RYB-HSV algorithm for color harmony:
    - Converts input color to RYB-HSV (Paletton's color space)
    - Rotates hue in RYB space for artistic color harmony
    - Applies Paletton's S/V adjustment based on natural values at each hue
    - Converts back using Paletton's ryb_hsv_to_rgb
    - Extracts OKLCH values directly from the Paletton sRGB outputs (accurate!)

    Args:
        hex_color: Hex color string like "#FF5500" or "FF5500"
        palette_set: "base", "adjacent", "triad", or "full"
        x_deg: Angle for adjacent/triad offsets
        include_complementary: Include complement hue

    Returns:
        BrandColorResult with the hex color as base and harmonics derived from its hue
    """
    # Convert input hex to RGB (0-255)
    r01, g01, b01 = rgb01_from_hex(hex_color)
    r255, g255, b255 = int(r01 * 255), int(g01 * 255), int(b01 * 255)

    # Convert to Paletton's RYB-HSV color space
    # This is the key - we use Paletton's algorithm, not standard HSV
    H_ryb, S, V = rgb_to_ryb_hsv(r255, g255, b255)

    # Build harmonic hues in RYB space
    ryb_hues_list: List[float] = [H_ryb]
    labels: List[str] = ["base"]

    if palette_set in ("adjacent", "full"):
        ryb_hues_list.append(mod360(H_ryb - x_deg))
        labels.append("adjacent_left")
        ryb_hues_list.append(mod360(H_ryb + x_deg))
        labels.append("adjacent_right")

    if include_complementary:
        ryb_hues_list.append(mod360(H_ryb + 180.0))
        labels.append("complementary")

    if palette_set in ("triad", "full"):
        ryb_hues_list.append(mod360(H_ryb + 180.0 - x_deg))
        labels.append("triad_left")
        ryb_hues_list.append(mod360(H_ryb + 180.0 + x_deg))
        labels.append("triad_right")

    # Dedupe hues while preserving order (based on RYB hues only)
    seen_hues: List[float] = []
    deduped_labels: List[str] = []
    deduped_ryb_hues: List[float] = []
    for lab, h_ryb in zip(labels, ryb_hues_list):
        if not any(
            abs(((h_ryb - s + 540.0) % 360.0) - 180.0) < 1e-7 for s in seen_hues
        ):
            deduped_labels.append(lab)
            deduped_ryb_hues.append(h_ryb)
            seen_hues.append(h_ryb)

    # Generate colors using Paletton's exact algorithm:
    # - Base color preserves original S and V
    # - Harmonic colors get S/V adjusted based on natural values at each hue
    srgb_list: List[Tuple[float, float, float]] = []
    p3_list: List[Tuple[float, float, float]] = []

    for i, h_ryb in enumerate(deduped_ryb_hues):
        if i == 0:
            # Base color: use original S and V exactly
            adj_s, adj_v = S, V
        else:
            # Harmonic colors: apply Paletton S/V adjustment
            # This preserves the "character" of the input color across hues
            adj_s, adj_v = paletton_sv_for_ryb_hue(h_ryb, S, V, H_ryb)

        # Convert using Paletton's ryb_hsv_to_rgb (returns 0-255)
        r_out, g_out, b_out = ryb_hsv_to_rgb(h_ryb, adj_s, adj_v)

        # Convert to 0-1 range for consistency
        rgb01 = (r_out / 255.0, g_out / 255.0, b_out / 255.0)
        srgb_list.append(rgb01)
        # For P3, we use the same RGB values (RYB-HSV doesn't distinguish gamuts)
        p3_list.append(rgb01)

    # Extract OKLCH values directly from Paletton's sRGB outputs
    # This is MORE ACCURATE than converting RYB hue → OKLCH hue separately,
    # because the actual color includes S/V adjustments that affect the hue slightly
    oklch_values_list: List[Tuple[float, float, float]] = []
    for r, g, b in srgb_list:
        L_color, C_color, H_color = srgb_to_oklch(r, g, b)
        oklch_values_list.append((L_color, C_color, H_color))

    # Use base color's L and C for the result (harmonics may have different L/C)
    base_L, base_C, _ = oklch_values_list[0]

    # Build result dictionaries
    hex_codes = {
        lab: hex_from_rgb01(r, g, b)
        for lab, (r, g, b) in zip(deduped_labels, srgb_list)
    }
    hex_codes_p3 = {
        lab: hex_from_rgb01(r, g, b) for lab, (r, g, b) in zip(deduped_labels, p3_list)
    }
    # Extract just the hues from OKLCH values for the oklch_hues dict
    oklch_hues_dict = {
        lab: H for lab, (_, _, H) in zip(deduped_labels, oklch_values_list)
    }
    srgb_values = {lab: rgb for lab, rgb in zip(deduped_labels, srgb_list)}
    p3_values = {lab: rgb for lab, rgb in zip(deduped_labels, p3_list)}

    return BrandColorResult(
        primary_ryb_hue=H_ryb,
        oklch_hues=oklch_hues_dict,
        L=base_L,
        C=base_C,
        hex_codes=hex_codes,
        hex_codes_p3=hex_codes_p3,
        srgb_values=srgb_values,
        p3_values=p3_values,
        labels=deduped_labels,
    )


# ---------- Main pipeline ----------


def main() -> None:
    p = argparse.ArgumentParser(
        description=(
            "Compute brand primary color and a chosen harmonic set from RYB hue "
            "mix, mapping to OKLCH with constant tone (L) and chroma (C) "
            "without clipping."
        )
    )
    p.add_argument(
        "--hue",
        action="append",
        required=True,
        help=(
            "Hue item (repeat 1–3 times). Form: 'Name:Weight'. "
            "Names: Red, Orange, Yellow, Green, Blue, Purple."
        ),
    )
    p.add_argument(
        "--chroma",
        type=int,
        default=50,
        help="Chroma intent 0–100 (0=gray, 100=max vivid). Default 50.",
    )
    p.add_argument(
        "--tone",
        type=int,
        default=50,
        help=(
            "Tone/Lightness intent 0–100 "
            "(0=near-black, 50=mid, 100=near-white). Default 50."
        ),
    )
    p.add_argument(
        "--set",
        choices=["base", "adjacent", "triad", "full"],
        default="full",
        help=(
            "Palette composition relative to base hue. "
            "'base' (1), 'adjacent' (base±X), 'triad' (180±X), "
            "'full' (adjacent + triad). Base is always included."
        ),
    )
    p.add_argument(
        "--x",
        type=float,
        default=30.0,
        help="Angle X in degrees for adjacent/triad offsets. Default 30.",
    )
    p.add_argument(
        "--include-complementary",
        action="store_true",
        help="Also include the complementary hue (base+180°).",
    )
    p.add_argument(
        "--chroma-scope",
        choices=["harmonics", "global"],
        default="harmonics",
        help=(
            "Pick common chroma from only the hues in the palette (harmonics) "
            "or from the entire 360° wheel at this tone (global)."
        ),
    )
    p.add_argument(
        "--chroma-margin",
        type=float,
        default=0.98,
        help=(
            "Safety margin multiplier for Cmax to avoid edge-of-gamut issues. "
            "Default 0.98."
        ),
    )
    p.add_argument(
        "--global-sample-deg",
        type=int,
        default=2,
        help="Sampling step (degrees) for global chroma scope. Default 2.",
    )
    p.add_argument(
        "--plain",
        action="store_true",
        help=(
            "Print only the HEX colors (space-separated) to stdout. "
            "Logs still go to stderr (use --quiet to silence)."
        ),
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress logs on stderr.",
    )
    args = p.parse_args()

    quiet = args.quiet

    if not (1 <= len(args.hue) <= 3):
        raise SystemExit(
            f"Error: Provide between 1 and 3 --hue items (got {len(args.hue)})."
        )

    try:
        parsed = [parse_hue_arg(s) for s in args.hue]
    except Exception as e:
        raise SystemExit(f"Error parsing --hue: {e}")

    # Log input summary
    log("▶ Parsing inputs…", quiet)
    for i, (name, weight) in enumerate(parsed, 1):
        log(f"  {i}. {name:7s} weight {weight:.2f}", quiet)
    log(f"  chroma_intent: {args.chroma}", quiet)
    log(f"  tone_intent:   {args.tone}", quiet)
    log(
        f"  set: {args.set}, X: {args.x}°, "
        f"include_complementary: {bool(args.include_complementary)}",
        quiet,
    )
    log(
        f"  chroma_scope: {args.chroma_scope}, "
        f"margin: {args.chroma_margin}, global_step: {args.global_sample_deg}°",
        quiet,
    )

    # Compute brand colors using the extracted function
    log("▶ Computing brand colors…", quiet)
    try:
        result = compute_brand_colors(
            hue_weights=parsed,
            chroma_intent=args.chroma,
            tone_intent=args.tone,
            palette_set=args.set,
            x_deg=args.x,
            include_complementary=args.include_complementary,
            chroma_scope=args.chroma_scope,
            chroma_margin=args.chroma_margin,
            global_sample_deg=args.global_sample_deg,
        )
    except ValueError as e:
        raise SystemExit(f"Error: {e}")

    log(f"  Primary RYB hue: {result.primary_ryb_hue:.2f}°", quiet)
    log(f"  L (tone): {result.L:.4f}", quiet)
    log(f"  C (chroma): {result.C:.4f}", quiet)
    for label in result.labels:
        h_oklch = result.oklch_hues[label]
        log(f"  {label:18s}: OKLCH hue {h_oklch:7.2f}°", quiet)

    # Output (ordered labels)
    if args.plain:
        hex_list = [result.hex_codes[label] for label in result.labels]
        print(" ".join(hex_list))
    else:
        print("Primary brand color palette (HEX):")
        for label in result.labels:
            print(f"  {label:18s}: {result.hex_codes[label]}")
        print(f"\nTone L: {result.L:.4f}  Chroma C: {result.C:.4f}")

    log("✔ Done.", quiet)


if __name__ == "__main__":
    main()
