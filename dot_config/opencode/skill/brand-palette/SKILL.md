---
name: brand-palette
description: |
  Brand color discovery and palette generation skill. This skill should be used when
  helping users create brand color palettes, design systems, or Tailwind color configs.
  It guides through hue selection (RYB color wheel), chroma/tone decisions, and
  generates Obsidian-compatible palette reports with APCA accessibility validation.
  Also supports starting from an existing hex color for refinement workflows.
  Triggers: "brand colors", "palette", "color scheme", "design system colors",
  "Tailwind colors", "generate palette from hex", or when users describe brand values
  that imply color decisions.
---

# Brand Palette

## Overview

This skill guides brand color discovery and generates comprehensive palette reports.
It walks through understanding brand identity, selecting hues from the RYB color wheel,
setting chroma/tone preferences, then generates Obsidian-compatible markdown with
full tonal scales (50-950), Tailwind configs, and APCA contrast validation.

**Two entry points:**
1. **Discovery flow** - Guide users through brand identity → hue selection → palette
2. **Hex refinement flow** - Start from an existing hex color (user already has a color they like)

## When to Use

- User wants to create a brand color palette or design system
- User needs Tailwind color configuration for a project
- User describes brand values, personality, or identity that imply color decisions
- User mentions competitors' colors to differentiate from
- User asks about accessible/APCA-compliant color schemes
- User has an existing hex color and wants to generate a full palette from it
- User picked a color from a previous palette and wants to regenerate around it

## Scripts

Execute via `uv run`:

```bash
uv run {base_dir}/scripts/brand_report.py [options]
```

| Script | Description |
|--------|-------------|
| `brand_report.py` | Main entry point - generates palette reports |

### brand_report.py Options

| Option | Description |
|--------|-------------|
| `--name NAME` | Brand name (required) |
| `--hue NAME:WEIGHT` | Hue with weight, repeat 1-3 times (e.g., Blue:0.6) |
| `--hex COLOR` | Start from hex color (e.g., #015856). Overrides --hue/--chroma/--tone |
| `--chroma 0-100` | Chroma/saturation intent (default: 50) |
| `--tone 0-100` | Tone/lightness intent (default: 50) |
| `--gamut p3\|srgb` | Target color gamut (default: p3) |
| `--include-complement` | Include the complementary color (180° opposite in RYB) |
| `--auto-adjust` | Auto-adjust colors for APCA contrast |
| `--output PATH` | Output file path (required) |

## Workflow A: Brand Discovery (Full Process)

Use this when starting from scratch with a new brand.

### Phase 1: Understand the Brand

This phase is collaborative and iterative. Engage in genuine dialogue to understand
the brand before making color decisions. Do not rush through as a checklist.

**Key areas to explore:**

1. **Brand essence**: What does the brand represent? Core values, personality traits, 
   emotional associations? What feelings should the brand evoke?

2. **Industry/category**: Finance, health, entertainment, luxury, tech, sustainability?
   Industry norms provide useful starting points (but can be intentionally broken).

3. **Target audience**: Who is the primary audience? Consider age, sophistication level,
   cultural context, and what resonates with them visually.

4. **Competitive landscape**: Who are the direct competitors? Use web search tools or
   subagents to research what colors dominate the competitive space. The goal is not
   to avoid these colors entirely, but to understand existing associations. A competitor
   strongly associated with blue doesn't mean blue is off-limits—it means choosing blue
   requires intentional differentiation or acceptance of the association.

5. **Existing constraints**: Any existing brand colors, logo colors, or assets that
   must be respected or harmonized with?

**Guidance:**
- If the user provides a detailed brief upfront, extract these elements and confirm understanding
- If information is sparse, ask targeted follow-up questions
- Summarize findings before proceeding to hue selection
- This phase may take several exchanges—that's expected and valuable

**⚠️ CHECKPOINT: Do NOT proceed to Phase 2 until the user explicitly confirms understanding of their brand. Present a summary of findings and wait for approval.**

### Phase 2: Select Hues

The palette system uses 6 anchor hues from the RYB color wheel. Select 1-3 hues
with weights that reflect their relative importance to the brand identity.

**Available Hues and Brand Associations:**

| Hue | Associations |
|-----|--------------|
| **Red** | Energy, passion, urgency, bold, confident, pioneering, excitement, youthful, active, powerful |
| **Orange** | Warmth, friendly, approachable, cheerful, creative, social, inviting, clarity, fun, optimistic |
| **Yellow** | Joy, optimism, sunshine, energetic, youthful, happy, cheerful, bright, summer, playful |
| **Green** | Nature, growth, health, trust, balance, safety, environmental, organic, peaceful, wealth |
| **Blue** | Trust, stability, calm, professional, secure, reliable, depth, progress, responsible, tranquil |
| **Purple** | Luxury, creativity, wisdom, elegance, ambition, noble, imaginative, mystical, sophisticated |

**Selection guidance:**

- **Single hue (weight 1.0)**: Strong, focused brand identity. Best when one association dominates.
- **Two hues (e.g., 0.6/0.4)**: Blended identity. Primary hue leads, secondary adds nuance.
- **Three hues (e.g., 0.5/0.3/0.2)**: Complex identity. Use sparingly; can dilute focus.

**Industry starting points** (guidance, not rules):

| Industry | Common Hues | Notes |
|----------|-------------|-------|
| Finance/Enterprise | Blue, Green | Trust, stability, growth |
| Health/Wellness | Green, Blue | Nature, calm, trust |
| Luxury/Premium | Purple, restrained Red | Elegance, sophistication |
| Food/Retail | Orange, Red, Yellow | Energy, appetite, warmth |
| Tech/SaaS | Blue, Purple | Trust, innovation |
| Sustainability/Eco | Green | Nature, environmental |
| Entertainment/Youth | Yellow, Orange, Red | Energy, fun, excitement |

**Discussion points:**
- Which associations from Phase 1 map most strongly to these hues?
- Does the competitive landscape suggest differentiation opportunities?
- Are there cultural considerations for the target audience?

**⚠️ CHECKPOINT: Propose hue selection with weights and reasoning. Do NOT proceed to Phase 3 until the user confirms the hue selection.**

### Phase 3: Set Chroma and Tone

After hue selection, determine the chroma (saturation) and tone (lightness) intents.
Both use a 0-100 scale and are independent of hue choice.

**Chroma (Vividness): 0-100**

| Range | Feel | Brand signals |
|-------|------|---------------|
| 20-40 | Muted, sophisticated, calm | Luxury, premium, minimalist, formal, reserved |
| 40-60 | Balanced, professional | Enterprise, finance, healthcare, government |
| 60-80 | Vibrant, energetic | Consumer tech, retail, entertainment, youth |
| 80-100 | Bold, attention-grabbing | Promotions, sports, disruptive startups |

*Higher chroma = more saturated, energetic, youthful*
*Lower chroma = more muted, sophisticated, calm*

**Tone (Lightness): 0-100**

| Range | Feel | Brand signals |
|-------|------|---------------|
| 30-45 | Dark, weighty, authoritative | Luxury, power, prestige, serious |
| 45-55 | Balanced, versatile | Most professional contexts, enterprise |
| 55-70 | Light, friendly, approachable | Wellness, consumer, inclusive, optimistic |
| 70-85 | Airy, soft, gentle | Lifestyle, wellness, feminine products |

*Higher tone = lighter, more approachable, open*
*Lower tone = darker, more authoritative, weighty*

**Discussion points:**
- What emotional register should the brand colors strike?
- Is the brand meant to feel approachable or authoritative?
- Should colors command attention or recede into sophistication?
- Will colors be used primarily for UI elements, marketing, or both?

**⚠️ CHECKPOINT: Propose chroma and tone values with reasoning. Do NOT proceed to Phase 4 until the user confirms these values.**

### Phase 4: Confirm Before Generation

Before generating the palette, present a summary of all choices for final approval.

**Summary template:**

```
Brand: [name]
Hues: [Hue1:weight1], [Hue2:weight2], ...
Chroma: [value] ([feel description])
Tone: [value] ([feel description])
Gamut: [p3 or srgb]
APCA Auto-Adjust: [yes/no]
```

**Additional options to confirm:**

- **Gamut**: Display P3 (wider, for modern displays) or sRGB (universal compatibility)
  - Default to P3 unless user needs maximum browser/device compatibility
- **APCA Auto-Adjust**: Automatically adjust colors that fail accessibility contrast
  - Recommended: yes (ensures all colors meet APCA Lc 60 threshold)

**Example summary:**

```
Brand: Acme Corp
Hues: Blue:0.6, Purple:0.4
Chroma: 55 (balanced, professional)
Tone: 50 (versatile, mid-range)
Gamut: Display P3
APCA Auto-Adjust: yes
```

**⚠️ CRITICAL: Wait for explicit user confirmation before proceeding. Do NOT generate the palette until the user approves the summary.**

**Generate command (only after approval):**

```bash
uv run {base_dir}/scripts/brand_report.py \
    --name "Brand Name" \
    --hue Blue:0.6 --hue Purple:0.4 \
    --chroma 55 \
    --tone 50 \
    --gamut p3 \
    --auto-adjust \
    --output thoughts/shared/brand/YYYY-MM-DD_brand-name_palette.md
```

### Phase 5: Review and Iterate

After generation:
- Review the generated report with the user
- The report can be opened in Obsidian to preview color swatches
- Tailwind configs can be copied directly into `tailwind.config.js`
- If adjustments are needed, re-run discovery or tweak parameters
- Use `--hex` to refine: pick a specific color from the palette and regenerate around it

## Workflow B: Hex Refinement (Quick Start)

Use this when the user already has a specific color they want to build from:
- They have an existing brand color
- They picked a color from a previous palette
- They refined a color externally and want to regenerate

### Process

1. **Get the hex color** from the user (e.g., #015856)

2. **Confirm the color** by showing what palette will be generated:
   - The hex becomes the primary anchor
   - L (lightness) and C (chroma) are extracted automatically
   - Harmonics (analogous, complements) are derived from the hue

3. **Generate directly:**

```bash
uv run {base_dir}/scripts/brand_report.py \
    --name "Brand Name" \
    --hex "#015856" \
    --gamut p3 \
    --auto-adjust \
    --output thoughts/shared/brand/YYYY-MM-DD_brand-name_palette.md
```

### Example Dialogue

**User:** "I like this teal color #015856 from the last palette. Can you regenerate around it?"

**Agent:** "I'll generate a new palette with #015856 as your primary anchor. This color has:
- Lightness: 41 (dark, authoritative)  
- Chroma: 19 (balanced, professional)
- Hue: 192° (teal/cyan)

Generating palette..."

```bash
uv run {base_dir}/scripts/brand_report.py \
    --name "Refined Brand" \
    --hex "#015856" \
    --output thoughts/shared/brand/2026-01-01_refined_palette.md
```

## Output

Reports include:
- Brand anchor colors at the chosen tone/chroma
- Max Chroma scales (bold, vibrant) with Tailwind config
- Even Chroma scales (harmonious, balanced) with Tailwind config
- All scales in Obsidian palette plugin format
- Metadata table with generation parameters

**Output location:** `thoughts/shared/brand/YYYY-MM-DD_brand-name_palette.md`

## Notes

**Script location**: Scripts are bundled with this skill at `{base_dir}/scripts/`.

## Troubleshooting

- **"Unknown hue name"**: Check spelling. Valid hues: Red, Orange, Yellow, Green, Blue, Purple
- **Colors look clipped**: Try reducing chroma or switching gamut from p3 to srgb
- **Report not rendering in Obsidian**: Ensure the Obsidian Palette plugin is installed

## Iteration Tips

- Small chroma/tone adjustments (±5-10) can significantly change the feel
- If colors feel too bold, reduce chroma before changing hues
- If colors feel too dark/light, adjust tone rather than chroma
- Use `--hex` to refine: pick a color from generated palette, regenerate around it
