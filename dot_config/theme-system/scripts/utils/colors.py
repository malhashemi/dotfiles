"""Color conversion and manipulation utilities"""


def hex_to_argb(hex_color: str, alpha: str = "ff") -> str:
    """Convert #RRGGBB to 0xAARRGGBB format
    
    Args:
        hex_color: Hex color string (with or without #)
        alpha: Alpha channel as hex (00-FF), default FF (opaque)
        
    Returns:
        Color in 0xAARRGGBB format
        
    Examples:
        >>> hex_to_argb("#1e1e2e")
        '0xff1e1e2e'
        >>> hex_to_argb("cba6f7", "a5")
        '0xa5cba6f7'
    """
    hex_clean = hex_color.lstrip("#")
    return f"0x{alpha}{hex_clean}"


def opacity_to_alpha(opacity_percent: int, format: str = "hex") -> str | float:
    """Convert 0-100 opacity percentage to alpha value
    
    Args:
        opacity_percent: 0-100 where 0=transparent, 100=opaque
        format: Output format - 'hex' (0xNN) or 'float' (0.0-1.0)
        
    Returns:
        Alpha value in requested format
        
    Examples:
        >>> opacity_to_alpha(65, "hex")
        '0xa6'
        >>> opacity_to_alpha(65, "float")
        0.65
        >>> opacity_to_alpha(0, "hex")
        '0x00'
        >>> opacity_to_alpha(100, "float")
        1.0
    """
    if format == "hex":
        alpha_int = int(opacity_percent * 255 / 100)
        return f"0x{alpha_int:02x}"
    elif format == "float":
        return opacity_percent / 100.0
    else:
        raise ValueError(f"Invalid format: {format}. Use 'hex' or 'float'")
