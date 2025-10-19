"""Theme data extraction and normalization utilities"""


def get_material_colors(theme_data: dict) -> dict:
    """Get Material Design 3 colors from theme data
    
    Args:
        theme_data: Theme configuration dictionary
        
    Returns:
        Dictionary of Material Design 3 colors
        
    Raises:
        KeyError: If theme data is missing required fields
    """
    theme = theme_data.get("theme", {})
    material = theme.get("material", {})
    
    if not material:
        raise KeyError("No Material Design 3 colors found in theme data")
    
    return material


def get_catppuccin_colors(theme_data: dict) -> dict:
    """Get Catppuccin colors from theme data
    
    Args:
        theme_data: Theme configuration dictionary
        
    Returns:
        Dictionary of Catppuccin colors
        
    Raises:
        KeyError: If theme data is missing required fields
    """
    theme = theme_data.get("theme", {})
    colors = theme.get("colors", {})
    
    if not colors:
        raise KeyError("No Catppuccin colors found in theme data")
    
    return colors


def is_dynamic_theme(theme_data: dict) -> bool:
    """Check if theme is dynamic (Material You)
    
    Args:
        theme_data: Theme configuration dictionary
        
    Returns:
        True if dynamic theme, False otherwise
    """
    theme = theme_data.get("theme", {})
    return theme.get("name") == "dynamic"


def get_theme_variant(theme_data: dict) -> str:
    """Get theme variant (light/dark/amoled)
    
    Args:
        theme_data: Theme configuration dictionary
        
    Returns:
        Theme variant string
    """
    theme = theme_data.get("theme", {})
    return theme.get("variant", "dark")


def map_catppuccin_to_material(ctp: dict) -> dict:
    """Map Catppuccin colors to Material Design 3 schema
    
    This provides a consistent Material Design 3 color palette
    derived from Catppuccin colors, allowing static themes to use
    the same color keys as dynamic themes.
    
    Args:
        ctp: Dictionary of Catppuccin colors
        
    Returns:
        Dictionary of Material Design 3 colors mapped from Catppuccin
        
    Example:
        >>> ctp = {"mauve": "#cba6f7", "base": "#1e1e2e", ...}
        >>> md3 = map_catppuccin_to_material(ctp)
        >>> md3["primary"]
        '#cba6f7'
    """
    return {
        # Primary colors (Mauve accent)
        "primary": ctp["mauve"],
        "on_primary": ctp["crust"],
        "primary_container": ctp["surface0"],
        "on_primary_container": ctp["text"],
        "primary_fixed": ctp["mauve"],
        "primary_fixed_dim": ctp["mauve"],
        "on_primary_fixed": ctp["crust"],
        "on_primary_fixed_variant": ctp["crust"],
        
        # Secondary colors (Blue)
        "secondary": ctp["blue"],
        "on_secondary": ctp["crust"],
        "secondary_container": ctp["surface0"],
        "on_secondary_container": ctp["text"],
        "secondary_fixed": ctp["blue"],
        "secondary_fixed_dim": ctp["blue"],
        "on_secondary_fixed": ctp["crust"],
        "on_secondary_fixed_variant": ctp["crust"],
        
        # Tertiary colors (Green)
        "tertiary": ctp["green"],
        "on_tertiary": ctp["crust"],
        "tertiary_container": ctp["surface0"],
        "on_tertiary_container": ctp["text"],
        "tertiary_fixed": ctp["green"],
        "tertiary_fixed_dim": ctp["green"],
        "on_tertiary_fixed": ctp["crust"],
        "on_tertiary_fixed_variant": ctp["crust"],
        
        # Error colors
        "error": ctp["red"],
        "on_error": ctp["crust"],
        "error_container": ctp["surface0"],
        "on_error_container": ctp["text"],
        
        # Background colors
        "background": ctp["base"],
        "on_background": ctp["text"],
        
        # Surface colors
        "surface": ctp["base"],
        "on_surface": ctp["text"],
        "surface_variant": ctp["surface0"],
        "on_surface_variant": ctp["subtext1"],
        "surface_dim": ctp["mantle"],
        "surface_bright": ctp["surface1"],
        "surface_container_lowest": ctp["crust"],
        "surface_container_low": ctp["mantle"],
        "surface_container": ctp["base"],
        "surface_container_high": ctp["surface0"],
        "surface_container_highest": ctp["surface1"],
        
        # Outline colors
        "outline": ctp["overlay0"],
        "outline_variant": ctp["surface2"],
        
        # Other
        "shadow": "#000000",
        "scrim": "#000000",
        "inverse_surface": ctp["text"],
        "inverse_on_surface": ctp["base"],
        "inverse_primary": ctp["mauve"],
    }
