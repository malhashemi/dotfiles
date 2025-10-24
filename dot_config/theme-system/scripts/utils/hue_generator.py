"""Generate 8 distinct hue families from Material Design 3 base colors"""

from typing import Dict, Tuple
from .color_math import (
    hex_to_hsl,
    hsl_to_hex,
    rotate_hue,
    adjust_lightness,
    adjust_saturation,
    contrast_ratio,
    ensure_contrast,
    blend_colors,
)


def generate_ide_palette(
    md3_colors: dict,
    variant: str,
    base_bg: str,
    base_text: str
) -> dict:
    """Generate 8-hue IDE color palette from MD3 base colors
    
    Strategy - MD3 FIRST:
    - ALWAYS use MD3 primary, secondary, tertiary as main colors (heavy usage)
    - ONLY adjust their lightness/saturation for readability, NEVER change hue
    - GENERATE missing colors (orange, yellow, green/pink, cyan) by rotating from MD3
    - Use smart conflict resolution - shift generated colors if they conflict
    
    This preserves wallpaper personality while ensuring 8 distinct hues.
    
    Args:
        md3_colors: Material Design 3 color dictionary
        variant: 'dark' or 'light'
        base_bg: Background color for contrast calculation
        base_text: Base text color for contrast calculation
        
    Returns:
        Dictionary mapping Catppuccin color names to hex values
    """
    # Extract MD3 anchor colors - these are SACRED, we keep their hues
    md3_primary = md3_colors.get('primary', '#6750A4')
    md3_secondary = md3_colors.get('secondary', '#625B71')
    md3_tertiary = md3_colors.get('tertiary', '#7D5260')
    md3_error = md3_colors.get('error', '#F2B8B5')
    
    # Extract hues - PRESERVE THESE
    primary_hue, primary_s, primary_l = hex_to_hsl(md3_primary)
    secondary_hue, secondary_s, secondary_l = hex_to_hsl(md3_secondary)
    tertiary_hue, tertiary_s, tertiary_l = hex_to_hsl(md3_tertiary)
    error_hue, error_s, error_l = hex_to_hsl(md3_error)
    
    # Collect MD3 hues for conflict detection
    md3_hues = [error_hue, primary_hue, secondary_hue, tertiary_hue]
    
    # Helper to check if a hue conflicts with existing hues
    def has_conflict(hue: float, existing: list, threshold: float = 15.0) -> bool:
        for e in existing:
            diff = abs(hue - e)
            # Account for circular wraparound (350° and 10° are close)
            if diff < threshold or diff > (360 - threshold):
                return True
        return False
    
    # Helper to find nearest free hue to target (with smaller shifts)
    def find_free_hue(target: float, existing: list, max_shift: int = 40) -> float:
        if not has_conflict(target, existing, threshold=15):
            return target
        # Try small shifts first (5°, 10°, 15°, etc.)
        for shift in range(5, max_shift, 5):
            for sign in [1, -1]:
                candidate = (target + sign * shift) % 360
                if not has_conflict(candidate, existing, threshold=15):
                    return candidate
        # If all else fails, use target anyway
        return target
    
    # Check if MD3 colors themselves conflict and adjust if needed
    # If primary and secondary are too close, shift secondary slightly
    secondary_hue_adjusted = secondary_hue
    if abs(secondary_hue - primary_hue) < 10:
        # MD3 gave us similar colors - shift secondary to create distinction
        # Try both directions, pick the one that doesn't conflict with other anchors
        shift_positive = (secondary_hue + 15) % 360
        shift_negative = (secondary_hue - 15) % 360
        
        if not has_conflict(shift_positive, [error_hue, primary_hue, tertiary_hue], threshold=10):
            secondary_hue_adjusted = shift_positive
        elif not has_conflict(shift_negative, [error_hue, primary_hue, tertiary_hue], threshold=10):
            secondary_hue_adjusted = shift_negative
        # else: keep original, accept the similarity
    
    # Determine what tertiary represents based on its hue
    # Check if tertiary is in the green range (90-150°)
    # If yes, use it as green; otherwise use it as pink and generate green
    is_tertiary_green = 90 <= tertiary_hue <= 150
    
    # Generate missing hues by rotating from MD3 colors
    if not is_tertiary_green:
        # Tertiary is NOT green - use it for pink/magenta family
        # Need to generate: orange, yellow, green, cyan
        
        # Orange: rotate from error (red) toward yellow
        orange_base = find_free_hue((error_hue + 30) % 360, md3_hues)
        
        # Yellow: rotate from error or tertiary
        yellow_base = find_free_hue(60, md3_hues + [orange_base])
        
        # Green: complement of tertiary, or standard position
        green_base = find_free_hue((tertiary_hue + 180) % 360, md3_hues + [orange_base, yellow_base])
        
        # Cyan: between green and secondary (blue)
        cyan_base = find_free_hue((green_base + secondary_hue_adjusted) / 2, md3_hues + [orange_base, yellow_base, green_base])
        
        # Use MD3 tertiary for pink, generated for green
        pink_hue = tertiary_hue
        green_hue = green_base
    else:
        # Tertiary is cool - use it for green family
        # Need to generate: orange, yellow, pink, cyan
        
        # Orange: rotate from error
        orange_base = find_free_hue((error_hue + 30) % 360, md3_hues)
        
        # Yellow: standard position
        yellow_base = find_free_hue(60, md3_hues + [orange_base])
        
        # Pink: complement of tertiary, or standard position  
        pink_base = find_free_hue((tertiary_hue + 180) % 360, md3_hues + [orange_base, yellow_base])
        
        # Cyan: between tertiary (green) and secondary (blue)
        cyan_base = find_free_hue((tertiary_hue + secondary_hue_adjusted) / 2, md3_hues + [orange_base, yellow_base, pink_base])
        
        # Use MD3 tertiary for green, generated for pink
        green_hue = tertiary_hue
        pink_hue = pink_base
    
    # Target lightness and saturation based on variant
    if variant == 'light':
        # Light mode: darker, more saturated accents
        accent_l = 50.0   # Medium lightness for readability
        accent_s = 70.0   # High saturation for vibrancy
    else:
        # Dark mode: lighter, softer accents
        accent_l = 75.0   # Light for visibility on dark
        accent_s = 60.0   # Moderate saturation to avoid eye strain
    
    # Generate 8 base colors
    # IMPORTANT: Use MD3 hues directly for primary/secondary/tertiary, only adjust L/S
    colors_base = {
        'red': hsl_to_hex((error_hue, accent_s, accent_l)),
        'orange': hsl_to_hex((orange_base, accent_s, accent_l)),
        'yellow': hsl_to_hex((yellow_base, accent_s, accent_l)),
        'green': hsl_to_hex((green_hue, accent_s, accent_l)),  # MD3 tertiary or generated
        'cyan': hsl_to_hex((cyan_base, accent_s, accent_l)),
        'blue': hsl_to_hex((secondary_hue_adjusted, accent_s, accent_l)),  # MD3 secondary (may be shifted slightly)
        'purple': hsl_to_hex((primary_hue, accent_s, accent_l)),  # ALWAYS use MD3 primary
        'pink': hsl_to_hex((pink_hue, accent_s, accent_l)),  # MD3 tertiary or generated
    }
    
    # Ensure WCAG contrast compliance
    # Text colors: WCAG AAA (7:1)
    # UI accents: WCAG AA (4.5:1)
    colors_contrast = {}
    for name, color in colors_base.items():
        if name in ['red']:  # Error text - strict AAA
            colors_contrast[name] = ensure_contrast(color, base_bg, target_ratio=7.0)
        else:  # UI elements - AA minimum
            colors_contrast[name] = ensure_contrast(color, base_bg, target_ratio=4.5)
    
    # Generate variations (lighter/darker variants)
    def lighter(color: str, amount: float = 10.0) -> str:
        h, s, l = hex_to_hsl(color)
        return hsl_to_hex((h, s, min(100, l + amount)))
    
    def darker(color: str, amount: float = 10.0) -> str:
        h, s, l = hex_to_hsl(color)
        return hsl_to_hex((h, s, max(0, l - amount)))
    
    # Map to Catppuccin's 26 color names
    palette = {
        # Base colors
        'base': base_bg,
        'mantle': md3_colors.get('surface_dim', darker(base_bg, 5)),
        'crust': md3_colors.get('surface_container_lowest', darker(base_bg, 10)),
        
        # Text hierarchy
        'text': base_text,
        'subtext1': blend_colors(base_text, base_bg, 0.7),  # 70% blend
        'subtext0': ensure_contrast(
            blend_colors(base_text, base_bg, 0.5),  # 50% blend
            base_bg,
            target_ratio=4.5
        ),
        
        # Surface variants
        'surface0': md3_colors.get('surface_container_low', lighter(base_bg, 5)),
        'surface1': md3_colors.get('surface_container', lighter(base_bg, 10)),
        'surface2': md3_colors.get('surface_container_high', lighter(base_bg, 15)),
        
        # Overlay/borders
        'overlay0': md3_colors.get('outline_variant', blend_colors(base_text, base_bg, 0.3)),
        'overlay1': md3_colors.get('outline', blend_colors(base_text, base_bg, 0.4)),
        'overlay2': blend_colors(base_text, base_bg, 0.5),
        
        # Accent colors - 8 distinct hues
        'red': colors_contrast['red'],
        'maroon': darker(colors_contrast['red'], 15),
        'peach': colors_contrast['orange'],
        'yellow': colors_contrast['yellow'],
        'green': colors_contrast['green'],
        'teal': lighter(colors_contrast['green'], 10),
        'sky': colors_contrast['cyan'],
        'sapphire': darker(colors_contrast['cyan'], 10),
        'blue': colors_contrast['blue'],
        'lavender': lighter(colors_contrast['purple'], 10),
        'mauve': colors_contrast['purple'],  # Primary accent
        'pink': colors_contrast['pink'],
        'flamingo': lighter(colors_contrast['pink'], 10),
        'rosewater': lighter(colors_contrast['pink'], 20),
    }
    
    return palette


def generate_semantic_ansi(palette: dict) -> dict:
    """Generate semantic ANSI color mapping
    
    ANSI colors MUST be semantically correct for terminal programs.
    
    Args:
        palette: Catppuccin color palette
        
    Returns:
        Dictionary mapping ANSI color names to hex values
    """
    return {
        # Normal colors (ANSI 0-7)
        'ansi_black': palette['surface0'],      # Not pure black
        'ansi_red': palette['red'],             # Actual red
        'ansi_green': palette['green'],         # Actual green (not pink!)
        'ansi_yellow': palette['yellow'],       # Actual yellow (not purple!)
        'ansi_blue': palette['blue'],           # Actual blue
        'ansi_magenta': palette['mauve'],       # Purple/magenta
        'ansi_cyan': palette['sky'],            # Actual cyan
        'ansi_white': palette['subtext1'],      # Light gray
        
        # Bright colors (ANSI 8-15)
        'ansi_bright_black': palette['overlay0'],
        'ansi_bright_red': palette['maroon'],
        'ansi_bright_green': palette['teal'],
        'ansi_bright_yellow': palette['peach'],
        'ansi_bright_blue': palette['sapphire'],
        'ansi_bright_magenta': palette['pink'],
        'ansi_bright_cyan': palette['lavender'],
        'ansi_bright_white': palette['text'],
    }


def validate_hue_distribution(palette: dict) -> dict:
    """Validate that palette has 8 distinct hue families
    
    Args:
        palette: Catppuccin color palette
        
    Returns:
        Dictionary with validation results and metrics
    """
    # Extract hues from key colors
    key_colors = ['red', 'peach', 'yellow', 'green', 'sky', 'blue', 'mauve', 'pink']
    hues = []
    
    for color_name in key_colors:
        if color_name in palette:
            h, s, l = hex_to_hsl(palette[color_name])
            hues.append((color_name, h, s, l))
    
    # Check for hue diversity (should span 360°)
    hue_values = [h for _, h, _, _ in hues]
    hue_range = max(hue_values) - min(hue_values)
    
    # Check for duplicates (hues within 10° are considered similar)
    # Note: Some wallpapers have similar MD3 colors (e.g. purple wallpaper has
    # primary and secondary both purple). We preserve these to maintain wallpaper
    # personality, so small differences are acceptable.
    duplicates = []
    for i, (name1, h1, _, _) in enumerate(hues):
        for name2, h2, _, _ in hues[i+1:]:
            diff = abs(h1 - h2)
            if diff < 10 or diff > 350:  # Account for wraparound, stricter threshold
                duplicates.append((name1, name2, h1, h2))
    
    return {
        'hue_count': len(hues),
        'hue_range': hue_range,
        'duplicates': duplicates,
        'is_valid': len(duplicates) == 0 and hue_range > 300,
        'hues': hues,
    }
