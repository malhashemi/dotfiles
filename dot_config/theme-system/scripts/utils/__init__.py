"""Theme system utilities"""

from .colors import hex_to_argb, opacity_to_alpha
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
from .system import detect_system_appearance, set_system_appearance, extract_colors_matugen
from .theme_data import (
    get_material_colors,
    get_catppuccin_colors,
    is_dynamic_theme,
    get_theme_variant,
    map_catppuccin_to_material,
)

__all__ = [
    # Color utilities
    "hex_to_argb",
    "opacity_to_alpha",
    # Color math
    "hex_to_hsl",
    "hsl_to_hex",
    "rotate_hue",
    "adjust_lightness",
    "adjust_saturation",
    "contrast_ratio",
    "ensure_contrast",
    "blend_colors",
    # System utilities
    "detect_system_appearance",
    "set_system_appearance",
    "extract_colors_matugen",
    # Theme data utilities
    "get_material_colors",
    "get_catppuccin_colors",
    "is_dynamic_theme",
    "get_theme_variant",
    "map_catppuccin_to_material",
]
