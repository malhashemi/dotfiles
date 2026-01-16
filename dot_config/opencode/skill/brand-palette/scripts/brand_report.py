#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Brand Palette Report Generator

Generate brand palette report in Obsidian-compatible markdown.

The report includes:
- Brand anchor colors at chosen tone/chroma
- Paletton Colors scales (exact input colors preserved)
- Even Chroma scales (harmonious and balanced)
- Tailwind configs for both modes
- Metadata table

All palette code blocks use the Obsidian palette plugin format.

Examples:
    uv run scripts/brand_report.py \\
        --name "Acme Corp" \\
        --hue Blue:0.6 --hue Purple:0.4 \\
        --chroma 62 --tone 52 \\
        --output thoughts/shared/brand/2026-01-01_acme-corp_palette.md

    uv run scripts/brand_report.py \\
        --name "EcoTech" \\
        --hue Green:0.7 --hue Blue:0.3 \\
        --chroma 45 --tone 55 \\
        --gamut p3 --auto-adjust \\
        --output thoughts/shared/brand/2026-01-01_ecotech_palette.md
"""

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Literal, cast

# Import from sibling modules
from brandcolor import (
    compute_brand_colors,
    brand_color_from_hex,
    brand_color_from_oklch,
    BrandColorResult,
)
from palette import (
    generate_palette,
    generate_palette_from_brand_color,
    find_anchor_level,
    auto_adjust_palette_contrast,
    Palette,
    LEVELS,
    Gamut,
)


# ========== Constants ==========

SCALE_ORDER = [
    "primary",
    "analogous-cool",
    "analogous-warm",
    "complement",
    "split-complement-cool",
    "split-complement-warm",
    "neutral",
]

SCALE_TITLES = {
    "primary": "Primary",
    "analogous-cool": "Analogous Cool",
    "analogous-warm": "Analogous Warm",
    "complement": "Complement",
    "split-complement-cool": "Split Cool",
    "split-complement-warm": "Split Warm",
    "neutral": "Neutral",
}

# Map brandcolor labels to palette labels
LABEL_MAP = {
    "base": "primary",
    "adjacent_left": "analogous-cool",
    "adjacent_right": "analogous-warm",
    "complementary": "complement",
    "triad_left": "split-complement-cool",
    "triad_right": "split-complement-warm",
}


# ========== Data Structures ==========


@dataclass
class ReportData:
    """All data needed for the report."""

    brand_name: str
    date: str
    hue_description: str  # "Blue (60%) + Purple (40%)"
    chroma_intent: int
    tone_intent: int
    gamut: Gamut
    auto_adjusted: bool
    anchor_level: int  # Level where brand color is placed (50-950)

    # Brand anchor colors
    brand_colors: BrandColorResult

    # Full palettes (three modes)
    input_palette: Palette  # Exact Paletton colors preserved
    even_palette: Palette  # Minimum chroma across all hues
    max_palette: Palette  # Maximum chroma per hue


# ========== Report Generation ==========


def format_tailwind_config(palette: Palette, use_oklch: bool = True) -> str:
    """Format palette as Tailwind CSS config."""
    lines = [
        "module.exports = {",
        "  theme: {",
        "    colors: {",
    ]

    def format_scale(name: str) -> List[str]:
        if name not in palette.scales:
            return []
        scale = palette.scales[name]
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

    for name in SCALE_ORDER:
        lines.extend(format_scale(name))

    lines.extend(
        [
            "    },",
            "  },",
            "};",
        ]
    )

    return "\n".join(lines)


def format_palette_block(hex_list: List[str], aliases: List[str]) -> str:
    """Format a palette code block for Obsidian."""
    lines = ["```palette"]
    lines.append(", ".join(hex_list))
    # Format aliases as JSON
    aliases_json = json.dumps(aliases)
    lines.append('{"aliases": ' + aliases_json + "}")
    lines.append("```")
    return "\n".join(lines)


def format_chroma_section(
    title: str,
    description: str,
    palette: Palette,
) -> List[str]:
    """Format a chroma mode section with sRGB preview and OKLCH config."""
    lines = []
    lines.append(f"## {title}")
    lines.append("")
    lines.append(description)
    lines.append("")

    # sRGB preview (this is what markdown can actually display)
    for name in SCALE_ORDER:
        if name not in palette.scales:
            continue
        scale = palette.scales[name]
        hex_list = scale.get_hex_list("srgb")

        lines.append(f"### {SCALE_TITLES[name]}")
        lines.append("")
        aliases = [str(level) for level in LEVELS]
        lines.append(format_palette_block(hex_list, aliases))
        lines.append("")

    # Tailwind config (OKLCH handles P3/sRGB automatically)
    lines.append(f"### Tailwind Config ({title})")
    lines.append("")
    lines.append(
        "> **Note**: The OKLCH values below are color-space aware. "
        "P3 displays will show richer colors; sRGB displays get automatic fallback."
    )
    lines.append("")
    lines.append("```javascript")
    lines.append(format_tailwind_config(palette, use_oklch=True))
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    return lines


def generate_report(data: ReportData) -> str:
    """Generate the markdown report."""
    lines = []

    # Header
    lines.append(f"# Brand Palette: {data.brand_name}")
    lines.append("")
    lines.append(f"> Generated: {data.date}")
    lines.append(f"> Primary Hue: {data.hue_description}")
    lines.append(
        f"> Chroma Intent: {data.chroma_intent} | Tone Intent: {data.tone_intent}"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Brand Colors section
    lines.append("## Brand Colors")
    lines.append("")
    lines.append("The anchor colors at your chosen tone with maximum chroma.")
    lines.append("")
    lines.append(
        "> These appear at **level {}** in the Paletton Colors palette below.".format(
            data.anchor_level
        )
    )
    lines.append("")

    # Get labels and hex codes from brand_colors (HSV-based harmonics)
    # These are the vibrant base colors with S/V preserved from the input
    labels = []
    hex_list_srgb = []
    for old_label in data.brand_colors.labels:
        new_label = LABEL_MAP.get(old_label, old_label)
        labels.append(SCALE_TITLES.get(new_label, new_label.title()))
        # Use the HSV-based brand colors directly (not palette-level colors)
        hex_list_srgb.append(data.brand_colors.hex_codes[old_label])

    lines.append(format_palette_block(hex_list_srgb, labels))
    lines.append("")

    # Add neutral endpoints to brand colors line for quick reference
    neutral_scale = data.input_palette.scales.get("neutral")
    if neutral_scale:
        neutral_light = neutral_scale.colors[50].hex_srgb
        neutral_dark = neutral_scale.colors[950].hex_srgb
        all_anchors = hex_list_srgb + [neutral_light, neutral_dark]
        lines.append("**With neutrals:**")
        lines.append("")
        lines.append(f"```palette\n{','.join(all_anchors)}\n```")
        lines.append("")

    # Full palette: all colors from all scales concatenated (from input palette)
    lines.append("**Full palette** (all scales concatenated):")
    lines.append("")
    all_colors = []
    for name in SCALE_ORDER:
        if name not in data.input_palette.scales:
            continue
        scale = data.input_palette.scales[name]
        hex_list = scale.get_hex_list("srgb")
        all_colors.extend(hex_list)
    lines.append(f"```palette\n{', '.join(all_colors)}\n```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Paletton Colors section (preserves exact input colors)
    lines.extend(
        format_chroma_section(
            "Paletton Colors",
            "Exact colors from Paletton harmonics. Your input color appears at its natural anchor level.",
            data.input_palette,
        )
    )

    # Max Chroma section
    lines.extend(
        format_chroma_section(
            "Max Chroma",
            "Maximum saturation per hue. Bold and vibrant.",
            data.max_palette,
        )
    )

    # Even Chroma section
    lines.extend(
        format_chroma_section(
            "Even Chroma",
            "Consistent saturation across all hues. Harmonious and balanced.",
            data.even_palette,
        )
    )

    # Usage Guide
    lines.append("## Usage Guide")
    lines.append("")
    lines.append("### Background Pairing")
    lines.append("")
    lines.append("Each shade level is designed for specific background contexts:")
    lines.append("")
    lines.append("| Levels | Use With | Purpose |")
    lines.append("|--------|----------|---------|")
    lines.append(
        "| **50-400** | Dark backgrounds (neutral-900, 950) | Light text/elements on dark surfaces |"
    )
    lines.append(
        "| **500** | Both light and dark | Versatile mid-tone, may need contrast check |"
    )
    lines.append(
        "| **600-950** | Light backgrounds (neutral-50, 100) | Dark text/elements on light surfaces |"
    )
    lines.append("")
    lines.append("### Contrast Requirements")
    lines.append("")
    lines.append(
        "All colors are validated against APCA (Accessible Perceptual Contrast Algorithm):"
    )
    lines.append("")
    lines.append(
        "- **Minimum Lc 60**: Required for body text and important UI elements"
    )
    lines.append("- **Lc 75+**: Recommended for smaller text (<18px)")
    lines.append(
        "- **Lc 45-60**: Acceptable for large text, icons, and decorative elements"
    )
    lines.append("")
    lines.append(
        "When `--auto-adjust` is enabled, colors that fail Lc 60 are automatically"
    )
    lines.append("adjusted by shifting lightness while preserving hue.")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Metadata
    lines.append("## Metadata")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("|----------|-------|")
    gamut_display = "Display P3" if data.gamut == "p3" else "sRGB"
    lines.append(f"| Gamut | {gamut_display} |")
    lines.append(f"| Anchor Level | {data.anchor_level} |")
    lines.append(f"| APCA Auto-Adjusted | {'Yes' if data.auto_adjusted else 'No'} |")
    lines.append("| Min Contrast (Lc) | 60 |")

    return "\n".join(lines)


# ========== CLI ==========


def main():
    parser = argparse.ArgumentParser(
        description="Generate brand palette report in Obsidian-compatible markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Basic report with hue selection
  brand_report.py --name "Acme Corp" --hue Blue:1 --output report.md

  # Multi-hue with full options
  brand_report.py --name "EcoTech" \\
      --hue Green:0.7 --hue Blue:0.3 \\
      --chroma 45 --tone 55 \\
      --gamut p3 --auto-adjust \\
      --output thoughts/shared/brand/2026-01-01_ecotech.md

  # Start from existing hex color
  brand_report.py --name "Refined Brand" \\
      --hex "#015856" \\
      --output thoughts/shared/brand/2026-01-01_refined.md
""",
    )

    parser.add_argument("--name", required=True, help="Brand name")
    parser.add_argument(
        "--hue",
        action="append",
        metavar="NAME:WEIGHT",
        help="Hue with weight (repeat 1-3 times). E.g., Blue:0.6. Required unless --hex is used.",
    )
    parser.add_argument(
        "--hex",
        metavar="COLOR",
        help="Start from existing hex color (e.g., #015856). Overrides --hue, --chroma, --tone.",
    )
    parser.add_argument(
        "--oklch",
        metavar="'L C H'",
        help="Start from OKLCH values (e.g., '0.72 0.12 201.7'). Overrides --hue, --chroma, --tone.",
    )
    parser.add_argument(
        "--chroma",
        type=int,
        default=50,
        help="Chroma intent 0-100 (default: 50)",
    )
    parser.add_argument(
        "--tone",
        type=int,
        default=50,
        help="Tone intent 0-100 (default: 50)",
    )
    parser.add_argument(
        "--gamut",
        choices=["p3", "srgb"],
        default="p3",
        help="Target gamut (default: p3)",
    )
    parser.add_argument(
        "--auto-adjust",
        action="store_true",
        help="Auto-adjust colors for APCA contrast",
    )
    parser.add_argument(
        "--include-complement",
        action="store_true",
        help="Include the complementary color (180° opposite in RYB)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output file path",
    )

    args = parser.parse_args()

    # Validate: either --hex, --oklch, or --hue is required
    if not args.hex and not args.oklch and not args.hue:
        parser.error("Either --hex, --oklch, or --hue is required")

    # Compute brand colors based on input mode
    if args.hex:
        # Start from existing hex color
        hex_color = args.hex.strip()
        print(f"Computing brand colors from hex {hex_color} for {args.name}...")
        brand_colors = brand_color_from_hex(
            hex_color, include_complementary=args.include_complement
        )
        hue_description = f"From hex: {hex_color}"
        # Override chroma/tone with actual values from hex
        chroma_intent = int(brand_colors.C / 0.37 * 100)  # Convert back to 0-100
        tone_intent = int(brand_colors.L * 100)
    elif args.oklch:
        # Start from OKLCH values
        oklch_str = args.oklch.strip()
        parts = oklch_str.split()
        if len(parts) != 3:
            parser.error("--oklch requires 3 values: 'L C H' (e.g., '0.72 0.12 201.7')")
        try:
            L, C, H = float(parts[0]), float(parts[1]), float(parts[2])
        except ValueError:
            parser.error("--oklch values must be numbers: 'L C H'")
        print(f"Computing brand colors from OKLCH({L}, {C}, {H}) for {args.name}...")
        brand_colors = brand_color_from_oklch(
            L, C, H, include_complementary=args.include_complement
        )
        hue_description = f"From OKLCH: L={L:.2f}, C={C:.2f}, H={H:.1f}"
        chroma_intent = int(C / 0.37 * 100)
        tone_intent = int(L * 100)
    else:
        # Parse hues from RYB color wheel
        hue_weights = []
        for h in args.hue:
            if ":" not in h:
                raise SystemExit(f"Invalid hue format '{h}'. Use Name:Weight")
            name, weight = h.split(":", 1)
            hue_weights.append((name.strip(), float(weight)))

        # Build hue description
        total_weight = sum(w for _, w in hue_weights)
        hue_parts = [
            f"{name} ({int(w / total_weight * 100)}%)" for name, w in hue_weights
        ]
        hue_description = " + ".join(hue_parts)
        chroma_intent = args.chroma
        tone_intent = args.tone

        # Compute brand colors
        print(f"Computing brand colors for {args.name}...")
        brand_colors = compute_brand_colors(
            hue_weights=hue_weights,
            chroma_intent=chroma_intent,
            tone_intent=tone_intent,
            include_complementary=args.include_complement,
        )

    # Find anchor level for this brand color
    anchor_level, _ = find_anchor_level(brand_colors.L)
    print(f"Anchor level: {anchor_level} (L={brand_colors.L:.3f})")

    # Generate all three palette modes
    print("Generating Paletton Colors palette (preserves exact input colors)...")
    input_palette = generate_palette_from_brand_color(
        brand_result=brand_colors,
        chroma_mode="input",
        gamut=args.gamut,
    )

    print("Generating Max Chroma palette...")
    max_palette = generate_palette_from_brand_color(
        brand_result=brand_colors,
        chroma_mode="max",
        gamut=args.gamut,
    )

    print("Generating Even Chroma palette...")
    even_palette = generate_palette_from_brand_color(
        brand_result=brand_colors,
        chroma_mode="even",
        gamut=args.gamut,
    )

    # Auto-adjust if requested
    if args.auto_adjust:
        print("Auto-adjusting for APCA contrast...")
        auto_adjust_palette_contrast(input_palette)
        auto_adjust_palette_contrast(max_palette)
        auto_adjust_palette_contrast(even_palette)

    # Build report data
    gamut: Gamut = cast(Gamut, args.gamut)
    data = ReportData(
        brand_name=args.name,
        date=str(date.today()),
        hue_description=hue_description,
        chroma_intent=chroma_intent,
        tone_intent=tone_intent,
        gamut=gamut,
        auto_adjusted=args.auto_adjust,
        anchor_level=anchor_level,
        brand_colors=brand_colors,
        input_palette=input_palette,
        even_palette=even_palette,
        max_palette=max_palette,
    )

    # Generate and write report
    print("Generating report...")
    report = generate_report(data)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report)
    print(f"Report written to: {args.output}")


if __name__ == "__main__":
    main()
