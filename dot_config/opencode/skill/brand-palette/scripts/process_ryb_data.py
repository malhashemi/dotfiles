#!/usr/bin/env python3
"""
Process Paletton RYB data to extract accurate RYB↔HSV mappings.

This script:
1. Reads the collected JSON data (72 RYB hues × 5 shades each)
2. Converts hex values to HSV
3. Builds the RYB→HSV hue mapping table
4. Analyzes S and V patterns across shades
5. Generates Python code for the new _RYB_HSV_ANCHORS

Usage:
    uv run scripts/process_ryb_data.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert hex string (no #) to RGB 0-255."""
    hex_str = hex_str.lstrip("#")
    return (
        int(hex_str[0:2], 16),
        int(hex_str[2:4], 16),
        int(hex_str[4:6], 16),
    )


def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """Convert RGB 0-255 to HSV (H in degrees, S and V in 0-1)."""
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    cmax = max(r_norm, g_norm, b_norm)
    cmin = min(r_norm, g_norm, b_norm)
    delta = cmax - cmin

    # Hue
    if delta < 1e-9:
        h = 0.0
    elif cmax == r_norm:
        h = 60.0 * (((g_norm - b_norm) / delta) % 6)
    elif cmax == g_norm:
        h = 60.0 * (((b_norm - r_norm) / delta) + 2)
    else:
        h = 60.0 * (((r_norm - g_norm) / delta) + 4)

    # Saturation
    s = 0.0 if cmax < 1e-9 else delta / cmax

    # Value
    v = cmax

    return (h % 360.0, s, v)


def hex_to_hsv(hex_str: str) -> Tuple[float, float, float]:
    """Convert hex to HSV."""
    r, g, b = hex_to_rgb(hex_str)
    return rgb_to_hsv(r, g, b)


def process_json_data(data: List[dict]) -> Dict[int, Dict]:
    """
    Process the JSON data to extract all RYB hue positions.

    Returns dict mapping RYB hue to:
    {
        "hsv_hue": float,  # HSV hue of the BASE shade
        "shades": [        # All 5 shades as (H, S, V)
            (h, s, v),
            ...
        ]
    }
    """
    results = {}

    for round_data in data:
        colors = round_data["colors"]

        for position in ["primary", "secondary_a", "secondary_b", "complement"]:
            color_data = colors[position]
            ryb_hue = color_data["ryb_hue"]
            shades = color_data["shades"]

            # Convert all 5 shades to HSV
            shade_hsv = [hex_to_hsv(shade) for shade in shades]

            # Base shade is index 2 (most saturated)
            base_hsv = shade_hsv[2]

            results[ryb_hue] = {
                "hsv_hue": base_hsv[0],
                "hsv_sat": base_hsv[1],
                "hsv_val": base_hsv[2],
                "shades": shade_hsv,
                "hex_base": shades[2],
            }

    return results


def analyze_v_patterns(results: Dict[int, Dict]) -> None:
    """Analyze V patterns to understand brightness variations."""
    print("\n" + "=" * 60)
    print("V (Value/Brightness) ANALYSIS")
    print("=" * 60)

    # Group by V value to see patterns
    v_by_hue = []
    for ryb_hue in sorted(results.keys()):
        data = results[ryb_hue]
        hsv_hue = data["hsv_hue"]
        v = data["hsv_val"]
        v_by_hue.append((ryb_hue, hsv_hue, v))

    print("\nRYB Hue → HSV Hue → V (brightness):")
    print("-" * 50)

    # Find min and max V
    min_v = min(x[2] for x in v_by_hue)
    max_v = max(x[2] for x in v_by_hue)
    min_v_entry = [x for x in v_by_hue if x[2] == min_v][0]

    for ryb_hue, hsv_hue, v in v_by_hue:
        bar = "█" * int(v * 30)
        marker = " ← MIN" if v == min_v else ""
        print(f"RYB {ryb_hue:3d}° → HSV {hsv_hue:6.1f}° : V={v:.3f} {bar}{marker}")

    print(f"\nV range: {min_v:.3f} to {max_v:.3f}")
    print(f"Minimum V at: RYB {min_v_entry[0]}° (HSV {min_v_entry[1]:.1f}°)")


def analyze_s_patterns(results: Dict[int, Dict]) -> None:
    """Analyze S patterns to understand saturation consistency."""
    print("\n" + "=" * 60)
    print("S (Saturation) ANALYSIS")
    print("=" * 60)

    s_values = [results[ryb]["hsv_sat"] for ryb in results]
    print(f"\nBase shade S range: {min(s_values):.3f} to {max(s_values):.3f}")
    print(
        f"S values are {'consistent' if max(s_values) - min(s_values) < 0.01 else 'variable'}"
    )

    # Show a few examples
    print("\nSample RYB → S values:")
    for ryb_hue in [0, 60, 120, 180, 240, 300]:
        if ryb_hue in results:
            s = results[ryb_hue]["hsv_sat"]
            print(f"  RYB {ryb_hue}°: S = {s:.3f}")


def analyze_shade_patterns(results: Dict[int, Dict]) -> None:
    """Analyze how S and V change across the 5 shades."""
    print("\n" + "=" * 60)
    print("SHADE PATTERN ANALYSIS (5 shades per hue)")
    print("=" * 60)

    # Take a sample hue to show the pattern
    sample_ryb = 0  # Red
    if sample_ryb in results:
        data = results[sample_ryb]
        print(f"\nExample: RYB {sample_ryb}° (Red)")
        print("Shade 0 = lightest, Shade 4 = darkest, Shade 2 = BASE")
        print("-" * 50)
        for i, (h, s, v) in enumerate(data["shades"]):
            marker = " ← BASE" if i == 2 else ""
            print(f"  Shade {i}: H={h:6.1f}° S={s:.3f} V={v:.3f}{marker}")

    # Check if shade patterns are consistent across hues
    print("\nShade S/V patterns across different RYB hues:")
    print("-" * 50)

    for ryb_hue in [0, 90, 180, 270]:
        if ryb_hue in results:
            data = results[ryb_hue]
            shades = data["shades"]
            # Show S progression
            s_vals = [f"{s:.2f}" for h, s, v in shades]
            v_vals = [f"{v:.2f}" for h, s, v in shades]
            print(
                f"  RYB {ryb_hue:3d}°: S=[{', '.join(s_vals)}] V=[{', '.join(v_vals)}]"
            )


def generate_anchor_code(results: Dict[int, Dict]) -> str:
    """Generate Python code for the new _RYB_HSV_ANCHORS."""
    lines = [
        "# RYB -> HSV anchors derived from Paletton.com data",
        "# 72 anchor points (every 5° from 0° to 355°)",
        "# Format: (RYB_hue, HSV_hue)",
        "_RYB_HSV_ANCHORS: List[Tuple[float, float]] = [",
    ]

    for ryb_hue in sorted(results.keys()):
        hsv_hue = results[ryb_hue]["hsv_hue"]
        lines.append(f"    ({ryb_hue:.1f}, {hsv_hue:.1f}),  # RYB {ryb_hue}°")

    # Add wrap-around point
    lines.append("    (360.0, 360.0),  # Wrap to Red")
    lines.append("]")

    return "\n".join(lines)


def generate_v_model_code(results: Dict[int, Dict]) -> str:
    """Generate Python code for the V model based on observed patterns."""
    # Build V lookup table
    v_data = []
    for ryb_hue in sorted(results.keys()):
        data = results[ryb_hue]
        hsv_hue = data["hsv_hue"]
        v = data["hsv_val"]
        v_data.append((ryb_hue, hsv_hue, v))

    lines = [
        "# V (brightness) values from Paletton at each RYB hue",
        "# The V reduction depends on BOTH input hue AND output hue",
        "# (RYB_hue, HSV_hue, V_natural)",
        "_RYB_V_TABLE: List[Tuple[float, float, float]] = [",
    ]

    for ryb_hue, hsv_hue, v in v_data:
        lines.append(f"    ({ryb_hue:.1f}, {hsv_hue:.1f}, {v:.3f}),")

    lines.append("]")

    return "\n".join(lines)


def main():
    # Load JSON data
    json_path = Path(__file__).parent.parent / "assets" / "ryb_data.json"

    if not json_path.exists():
        print(f"Error: JSON file not found at {json_path}", file=sys.stderr)
        sys.exit(1)

    with open(json_path) as f:
        data = json.load(f)

    print("=" * 60)
    print("PALETTON RYB DATA PROCESSOR")
    print("=" * 60)
    print(f"\nLoaded {len(data)} rounds of data")

    # Process data
    results = process_json_data(data)
    print(f"Extracted {len(results)} unique RYB hue positions")

    # Build RYB → HSV mapping table
    print("\n" + "=" * 60)
    print("RYB → HSV HUE MAPPING (base shades only)")
    print("=" * 60)

    for ryb_hue in sorted(results.keys()):
        data = results[ryb_hue]
        hsv_hue = data["hsv_hue"]
        # Show the delta for interesting points
        diff = hsv_hue - ryb_hue
        if abs(diff) > 180:
            diff = diff - 360 if diff > 0 else diff + 360
        print(f"RYB {ryb_hue:3d}° → HSV {hsv_hue:6.1f}° (Δ = {diff:+6.1f}°)")

    # Analyze patterns
    analyze_v_patterns(results)
    analyze_s_patterns(results)
    analyze_shade_patterns(results)

    # Generate code
    print("\n" + "=" * 60)
    print("GENERATED PYTHON CODE")
    print("=" * 60)

    print("\n# --- Anchor Table ---")
    print(generate_anchor_code(results))

    print("\n# --- V Model Table ---")
    print(generate_v_model_code(results))

    # Write mapping to file for reference
    output_path = Path(__file__).parent.parent / "assets" / "ryb_hsv_mapping.json"
    with open(output_path, "w") as f:
        json.dump(
            {str(k): v for k, v in sorted(results.items())},
            f,
            indent=2,
        )
    print(f"\nFull mapping saved to: {output_path}")


if __name__ == "__main__":
    main()
