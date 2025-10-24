"""Color mathematics for HSL manipulation and WCAG contrast calculation"""

from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple
    
    Args:
        hex_color: Hex color string (with or without #)
        
    Returns:
        Tuple of (r, g, b) values 0-255
    """
    hex_clean = hex_color.lstrip('#')
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    return (r, g, b)


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color
    
    Args:
        rgb: Tuple of (r, g, b) values 0-255
        
    Returns:
        Hex color string with #
    """
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def rgb_to_hsl(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert RGB to HSL
    
    Args:
        rgb: Tuple of (r, g, b) values 0-255
        
    Returns:
        Tuple of (h, s, l) where h is 0-360, s and l are 0-100
    """
    r, g, b = [x / 255.0 for x in rgb]
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2.0

    if max_c == min_c:
        h = s = 0.0  # achromatic
    else:
        d = max_c - min_c
        s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
        
        if max_c == r:
            h = (g - b) / d + (6.0 if g < b else 0.0)
        elif max_c == g:
            h = (b - r) / d + 2.0
        else:
            h = (r - g) / d + 4.0
        
        h *= 60.0
    
    return (h, s * 100.0, l * 100.0)


def hsl_to_rgb(hsl: Tuple[float, float, float]) -> Tuple[int, int, int]:
    """Convert HSL to RGB
    
    Args:
        hsl: Tuple of (h, s, l) where h is 0-360, s and l are 0-100
        
    Returns:
        Tuple of (r, g, b) values 0-255
    """
    h, s, l = hsl
    s /= 100.0
    l /= 100.0
    
    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p
    
    if s == 0:
        r = g = b = l  # achromatic
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, (h / 360.0) + 1/3)
        g = hue_to_rgb(p, q, h / 360.0)
        b = hue_to_rgb(p, q, (h / 360.0) - 1/3)
    
    return (int(r * 255), int(g * 255), int(b * 255))


def hex_to_hsl(hex_color: str) -> Tuple[float, float, float]:
    """Convert hex color to HSL
    
    Args:
        hex_color: Hex color string (with or without #)
        
    Returns:
        Tuple of (h, s, l) where h is 0-360, s and l are 0-100
    """
    return rgb_to_hsl(hex_to_rgb(hex_color))


def hsl_to_hex(hsl: Tuple[float, float, float]) -> str:
    """Convert HSL to hex color
    
    Args:
        hsl: Tuple of (h, s, l) where h is 0-360, s and l are 0-100
        
    Returns:
        Hex color string with #
    """
    return rgb_to_hex(hsl_to_rgb(hsl))


def rotate_hue(hex_color: str, degrees: float) -> str:
    """Rotate hue by specified degrees
    
    Args:
        hex_color: Hex color string
        degrees: Degrees to rotate (positive or negative)
        
    Returns:
        New hex color with rotated hue
    """
    h, s, l = hex_to_hsl(hex_color)
    h = (h + degrees) % 360.0
    return hsl_to_hex((h, s, l))


def adjust_lightness(hex_color: str, target_lightness: float) -> str:
    """Adjust color to target lightness percentage
    
    Args:
        hex_color: Hex color string
        target_lightness: Target lightness 0-100
        
    Returns:
        New hex color with adjusted lightness
    """
    h, s, l = hex_to_hsl(hex_color)
    return hsl_to_hex((h, s, target_lightness))


def adjust_saturation(hex_color: str, target_saturation: float) -> str:
    """Adjust color to target saturation percentage
    
    Args:
        hex_color: Hex color string
        target_saturation: Target saturation 0-100
        
    Returns:
        New hex color with adjusted saturation
    """
    h, s, l = hex_to_hsl(hex_color)
    return hsl_to_hex((h, target_saturation, l))


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate relative luminance per WCAG 2.1
    
    Args:
        rgb: Tuple of (r, g, b) values 0-255
        
    Returns:
        Relative luminance 0.0-1.0
    """
    r, g, b = [x / 255.0 for x in rgb]
    
    def adjust(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    r = adjust(r)
    g = adjust(g)
    b = adjust(b)
    
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """Calculate WCAG contrast ratio between two colors
    
    Args:
        fg_hex: Foreground hex color
        bg_hex: Background hex color
        
    Returns:
        Contrast ratio (1.0-21.0)
    """
    l1 = relative_luminance(hex_to_rgb(fg_hex))
    l2 = relative_luminance(hex_to_rgb(bg_hex))
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)


def ensure_contrast(
    fg_hex: str,
    bg_hex: str,
    target_ratio: float = 4.5,
    max_iterations: int = 20
) -> str:
    """Adjust foreground color to meet target contrast ratio
    
    Args:
        fg_hex: Foreground hex color to adjust
        bg_hex: Background hex color (fixed)
        target_ratio: Target WCAG contrast ratio
        max_iterations: Maximum adjustment iterations
        
    Returns:
        Adjusted foreground color that meets target ratio
    """
    ratio = contrast_ratio(fg_hex, bg_hex)
    
    if ratio >= target_ratio:
        return fg_hex
    
    h, s, l = hex_to_hsl(fg_hex)
    bg_lum = relative_luminance(hex_to_rgb(bg_hex))
    
    # Determine if we need lighter or darker foreground
    step = 2.0  # Lightness adjustment per iteration
    if bg_lum > 0.5:
        # Light background, need darker foreground
        direction = -1
    else:
        # Dark background, need lighter foreground
        direction = 1
    
    for _ in range(max_iterations):
        l = max(0, min(100, l + (step * direction)))
        fg_new = hsl_to_hex((h, s, l))
        ratio = contrast_ratio(fg_new, bg_hex)
        
        if ratio >= target_ratio:
            return fg_new
    
    # If can't meet target, return best attempt
    return hsl_to_hex((h, s, l))


def blend_colors(fg_hex: str, bg_hex: str, alpha: float) -> str:
    """Blend foreground color with background at given alpha
    
    Args:
        fg_hex: Foreground hex color
        bg_hex: Background hex color
        alpha: Alpha value 0.0-1.0 (1.0 = full fg, 0.0 = full bg)
        
    Returns:
        Blended hex color
    """
    fg_rgb = hex_to_rgb(fg_hex)
    bg_rgb = hex_to_rgb(bg_hex)
    
    r = int(fg_rgb[0] * alpha + bg_rgb[0] * (1 - alpha))
    g = int(fg_rgb[1] * alpha + bg_rgb[1] * (1 - alpha))
    b = int(fg_rgb[2] * alpha + bg_rgb[2] * (1 - alpha))
    
    return rgb_to_hex((r, g, b))
