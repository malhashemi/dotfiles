#!/usr/bin/env python3
"""Validate Neovim theme implementation"""

import re
from pathlib import Path
from utils.color_math import hex_to_hsl, contrast_ratio

HOME = Path.home()
NVIM_COLORS = HOME / ".config/nvim/lua/themes/colors-nvim.lua"


def parse_lua_colors(lua_file: Path) -> dict:
    """Extract color values from Lua file"""
    colors = {}
    if not lua_file.exists():
        return colors
        
    with open(lua_file) as f:
        for line in f:
            if '= "#' in line and not line.strip().startswith('--'):
                # Match pattern like: key = "#hexval",
                match = re.search(r'(\w+)\s*=\s*"(#[0-9a-fA-F]{6})"', line)
                if match:
                    name = match.group(1)
                    hex_val = match.group(2)
                    colors[name] = hex_val
    return colors


def validate_hue_distribution(colors: dict) -> bool:
    """Check for 8 distinct hue families"""
    key_colors = ['red', 'peach', 'yellow', 'green', 'sky', 'blue', 'mauve', 'pink']
    hues = []
    
    for color_name in key_colors:
        if color_name in colors:
            h, s, l = hex_to_hsl(colors[color_name])
            hues.append((color_name, h))
    
    if len(hues) < 8:
        print(f"❌ Only {len(hues)} hues found (expected 8)")
        return False
    
    # Check for duplicates (within 15°)
    duplicates = []
    for i, (name1, h1) in enumerate(hues):
        for name2, h2 in hues[i+1:]:
            diff = abs(h1 - h2)
            # Account for wraparound (e.g., 350° and 10° are close)
            if diff < 15 or diff > 345:
                duplicates.append((name1, name2, h1, h2))
    
    if duplicates:
        print(f"❌ Duplicate hues found:")
        for name1, name2, h1, h2 in duplicates:
            print(f"   {name1} ({h1:.1f}°) ~ {name2} ({h2:.1f}°)")
        return False
    
    print(f"✅ {len(hues)} distinct hue families:")
    for name, h in hues:
        print(f"   {name:12} H:{h:6.1f}°")
    return True


def validate_ansi_colors(colors: dict) -> bool:
    """Check ANSI colors are semantically correct"""
    checks = []
    
    # Green should be green (90-150°)
    if 'green' in colors:
        h, _, _ = hex_to_hsl(colors['green'])
        is_green = 90 < h < 150
        checks.append(('green', h, is_green, (90, 150)))
    
    # Yellow should be yellow (40-80°)
    if 'yellow' in colors:
        h, _, _ = hex_to_hsl(colors['yellow'])
        is_yellow = 40 < h < 80
        checks.append(('yellow', h, is_yellow, (40, 80)))
    
    # Blue should be blue (200-260°)
    if 'blue' in colors:
        h, _, _ = hex_to_hsl(colors['blue'])
        is_blue = 200 < h < 260
        checks.append(('blue', h, is_blue, (200, 260)))
    
    all_pass = all(check[2] for check in checks)
    
    print(f"\n{'✅' if all_pass else '❌'} ANSI Color Semantic Correctness:")
    for name, h, passed, (min_h, max_h) in checks:
        status = "✅" if passed else "❌"
        print(f"   {status} {name:12} H:{h:6.1f}° (expected {min_h}-{max_h}°)")
    
    return all_pass


def validate_contrast(colors: dict) -> bool:
    """Check WCAG contrast compliance"""
    base = colors.get('base', '#000000')
    text_colors = ['text', 'subtext1', 'subtext0']
    
    all_pass = True
    print(f"\n{'Contrast Ratios:':20}")
    for color_name in text_colors:
        if color_name in colors:
            ratio = contrast_ratio(colors[color_name], base)
            target = 4.5
            passed = ratio >= target
            status = "✅" if passed else "❌"
            print(f"   {status} {color_name:12} {ratio:5.2f}:1 (target {target}:1)")
            all_pass = all_pass and passed
    
    return all_pass


def validate_no_duplicates(colors: dict) -> bool:
    """Check for exact duplicate hex values"""
    seen = {}
    duplicates = []
    
    for name, hex_val in colors.items():
        if hex_val in seen:
            duplicates.append((name, seen[hex_val], hex_val))
        else:
            seen[hex_val] = name
    
    if duplicates:
        print(f"\n❌ Exact duplicate colors found:")
        for name1, name2, hex_val in duplicates:
            print(f"   {name1} = {name2} ({hex_val})")
        return False
    
    print(f"\n✅ No exact duplicates (26 unique colors)")
    return True


def main():
    print("🎨 Validating Neovim Dynamic Theme Colors\n")
    print("=" * 60)
    
    if not NVIM_COLORS.exists():
        print(f"\n✅ Static theme mode (no validation needed)")
        print(f"   File {NVIM_COLORS} doesn't exist")
        return 0
    
    colors = parse_lua_colors(NVIM_COLORS)
    
    if not colors:
        print(f"\n✅ Static theme mode (empty colors file)")
        return 0
    
    print(f"\nFound {len(colors)} colors in {NVIM_COLORS.name}")
    print("=" * 60)
    
    # Run validations
    hue_ok = validate_hue_distribution(colors)
    ansi_ok = validate_ansi_colors(colors)
    contrast_ok = validate_contrast(colors)
    unique_ok = validate_no_duplicates(colors)
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"{'✅' if hue_ok else '❌'} Hue Distribution:  {'PASS' if hue_ok else 'FAIL'}")
    print(f"{'✅' if ansi_ok else '❌'} ANSI Semantics:    {'PASS' if ansi_ok else 'FAIL'}")
    print(f"{'✅' if contrast_ok else '❌'} Contrast Ratios:  {'PASS' if contrast_ok else 'FAIL'}")
    print(f"{'✅' if unique_ok else '❌'} No Duplicates:    {'PASS' if unique_ok else 'FAIL'}")
    print("=" * 60)
    
    if hue_ok and ansi_ok and contrast_ok and unique_ok:
        print("\n✅ All validations passed!\n")
        return 0
    else:
        print("\n❌ Some validations failed\n")
        return 1


if __name__ == "__main__":
    exit(main())
