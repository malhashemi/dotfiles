#!/bin/bash
# Wallpaper manager integrated with theme system
# Based on original wallpaper-theme.sh but integrated into theme-system

# === CONFIGURATION ===
THEME_SYSTEM_DIR="$HOME/.config/theme-system"
WALLPAPER_DIR="$HOME/Pictures/Wallpapers"
CACHE_DIR="$THEME_SYSTEM_DIR/cache"
THUMBS_DIR="$CACHE_DIR/wallpaper-thumbs"
LOG_FILE="$CACHE_DIR/wallpaper.log"
CURRENT_FILE="$THEME_SYSTEM_DIR/state/current-wallpaper.txt"
STATE_DIR="$THEME_SYSTEM_DIR/state"

# Wallust configuration
WALLUST_CONFIG="$HOME/.config/wallust/wallust.toml"
WALLUST_CACHE="$HOME/.cache/wal"

# Create required directories
mkdir -p "$CACHE_DIR"
mkdir -p "$THUMBS_DIR"
mkdir -p "$STATE_DIR"
mkdir -p "$WALLUST_CACHE"

# === FUNCTIONS ===

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check_dependencies() {
    local missing_deps=()
    
    if ! command -v wallpaper &> /dev/null; then
        missing_deps+=("macos-wallpaper (install with: brew install wallpaper)")
    fi
    
    if ! command -v wallust &> /dev/null; then
        missing_deps+=("wallust (install with: brew install wallust)")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo "ERROR: Missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        return 1
    fi
    return 0
}

get_random_wallpaper() {
    local wallpapers=()
    
    # Find image files in root directory only
    while IFS= read -r -d '' file; do
        local filename=$(basename "$file")
        local extension="${filename##*.}"
        extension=$(echo "$extension" | tr '[:upper:]' '[:lower:]')
        
        case "$extension" in
            jpg|jpeg|png|heic|heif|webp|bmp|tiff|tif)
                wallpapers+=("$file")
                ;;
        esac
    done < <(find "$WALLPAPER_DIR" -maxdepth 1 -type f -print0 2>/dev/null)
    
    if [ ${#wallpapers[@]} -eq 0 ]; then
        echo "ERROR: No image files found in $WALLPAPER_DIR"
        return 1
    fi
    
    # Get random wallpaper
    local random_index=$((RANDOM % ${#wallpapers[@]}))
    echo "${wallpapers[$random_index]}"
}

apply_wallpaper() {
    local wallpaper="$1"
    
    if command -v wallpaper &> /dev/null; then
        wallpaper set "$wallpaper" 2>> "$LOG_FILE"
        return $?
    fi
    
    # Fallback to AppleScript
    osascript -e "tell application \"System Events\" to set picture of every desktop to \"$wallpaper\"" 2>> "$LOG_FILE"
    return $?
}

generate_dynamic_theme() {
    local wallpaper="$1"
    
    echo "🎨 Generating dynamic theme from wallpaper..."
    
    # Run wallust to generate colors
    if command -v wallust &> /dev/null; then
        wallust run "$wallpaper" >> "$LOG_FILE" 2>&1
        
        # Convert wallust output to our theme format
        if [ -f "$HOME/.cache/wal/colors.json" ]; then
            # Parse wallust colors and create dynamic theme
            python3 "$THEME_SYSTEM_DIR/scripts/convert-wallust-theme.py"
        fi
    fi
    
    # Update theme state to dynamic
    echo "dynamic" > "$STATE_DIR/current-theme.txt"
    
    # Trigger theme manager to apply dynamic theme
    "$THEME_SYSTEM_DIR/theme-manager.py" set dynamic
    
    return 0
}

# === MAIN ===

case "$1" in
    random)
        if ! check_dependencies; then
            exit 1
        fi
        
        WALLPAPER=$(get_random_wallpaper)
        if [ -z "$WALLPAPER" ]; then
            exit 1
        fi
        
        echo "📸 Selected: $(basename "$WALLPAPER")"
        
        if apply_wallpaper "$WALLPAPER"; then
            echo "$WALLPAPER" > "$CURRENT_FILE"
            echo "✅ Wallpaper applied"
            
            if [ "$2" = "--theme" ]; then
                generate_dynamic_theme "$WALLPAPER"
            fi
        else
            echo "❌ Failed to apply wallpaper"
            exit 1
        fi
        ;;
        
    set)
        if [ -z "$2" ]; then
            echo "Usage: $0 set <wallpaper-path> [--theme]"
            exit 1
        fi
        
        if [ ! -f "$2" ]; then
            echo "ERROR: File not found: $2"
            exit 1
        fi
        
        if apply_wallpaper "$2"; then
            echo "$2" > "$CURRENT_FILE"
            echo "✅ Wallpaper applied"
            
            if [ "$3" = "--theme" ]; then
                generate_dynamic_theme "$2"
            fi
        else
            echo "❌ Failed to apply wallpaper"
            exit 1
        fi
        ;;
        
    current)
        if [ -f "$CURRENT_FILE" ]; then
            cat "$CURRENT_FILE"
        else
            echo "No wallpaper set"
        fi
        ;;
        
    theme)
        if [ -f "$CURRENT_FILE" ]; then
            CURRENT=$(cat "$CURRENT_FILE")
            generate_dynamic_theme "$CURRENT"
        else
            echo "No current wallpaper to generate theme from"
            exit 1
        fi
        ;;
        
    *)
        echo "Wallpaper Manager - Part of Theme System"
        echo ""
        echo "Usage:"
        echo "  $0 random [--theme]    - Set random wallpaper (optionally generate theme)"
        echo "  $0 set <path> [--theme] - Set specific wallpaper"
        echo "  $0 current              - Show current wallpaper"
        echo "  $0 theme                - Generate theme from current wallpaper"
        ;;
esac