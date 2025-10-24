#!/usr/bin/env python3
"""Unit tests for color math utilities"""

from utils.color_math import (
    hex_to_hsl,
    hsl_to_hex,
    rotate_hue,
    adjust_lightness,
    contrast_ratio,
)


def test_hex_to_hsl():
    # Pure red
    h, s, l = hex_to_hsl("#ff0000")
    assert abs(h - 0.0) < 1.0
    assert abs(s - 100.0) < 1.0
    assert abs(l - 50.0) < 1.0
    
    # Pure green
    h, s, l = hex_to_hsl("#00ff00")
    assert abs(h - 120.0) < 1.0
    assert abs(s - 100.0) < 1.0
    assert abs(l - 50.0) < 1.0
    
    # Pure blue
    h, s, l = hex_to_hsl("#0000ff")
    assert abs(h - 240.0) < 1.0
    assert abs(s - 100.0) < 1.0
    assert abs(l - 50.0) < 1.0
    
    print("✓ hex_to_hsl tests passed")


def test_hsl_to_hex():
    # Red
    assert hsl_to_hex((0, 100, 50)) == "#ff0000"
    # Green
    assert hsl_to_hex((120, 100, 50)) == "#00ff00"
    # Blue
    assert hsl_to_hex((240, 100, 50)) == "#0000ff"
    
    print("✓ hsl_to_hex tests passed")


def test_rotate_hue():
    # Red to green (120° rotation)
    result = rotate_hue("#ff0000", 120)
    assert result == "#00ff00", f"Expected #00ff00, got {result}"
    
    # Green to blue (120° rotation)
    result = rotate_hue("#00ff00", 120)
    assert result == "#0000ff", f"Expected #0000ff, got {result}"
    
    # Negative rotation (green to red)
    result = rotate_hue("#00ff00", -120)
    assert result == "#ff0000", f"Expected #ff0000, got {result}"
    
    print("✓ rotate_hue tests passed")


def test_adjust_lightness():
    # Make red darker (L:25%)
    result = adjust_lightness("#ff0000", 25)
    h, s, l = hex_to_hsl(result)
    assert abs(l - 25.0) < 1.0, f"Expected L:25, got L:{l}"
    
    # Make red lighter (L:75%)
    result = adjust_lightness("#ff0000", 75)
    h, s, l = hex_to_hsl(result)
    assert abs(l - 75.0) < 1.0, f"Expected L:75, got L:{l}"
    
    print("✓ adjust_lightness tests passed")


def test_contrast_ratio():
    # Black on white should be ~21:1
    ratio = contrast_ratio("#000000", "#ffffff")
    assert abs(ratio - 21.0) < 0.1, f"Expected ~21:1, got {ratio:.2f}:1"
    
    # White on black (same ratio)
    ratio = contrast_ratio("#ffffff", "#000000")
    assert abs(ratio - 21.0) < 0.1, f"Expected ~21:1, got {ratio:.2f}:1"
    
    # Same color should be 1:1
    ratio = contrast_ratio("#ff0000", "#ff0000")
    assert abs(ratio - 1.0) < 0.01, f"Expected 1:1, got {ratio:.2f}:1"
    
    print("✓ contrast_ratio tests passed")


if __name__ == "__main__":
    test_hex_to_hsl()
    test_hsl_to_hex()
    test_rotate_hue()
    test_adjust_lightness()
    test_contrast_ratio()
    print("\n✅ All color math tests passed!")
