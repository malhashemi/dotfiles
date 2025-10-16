#!/usr/bin/env zsh
# Custom Shell Completions
# Theme system and other custom command completions

# ============================================================================
# Theme Command Completions
# ============================================================================

_theme() {
    local -a commands
    commands=(
        'set:Set theme (mocha, latte, frappe, macchiato, dynamic)'
        'toggle:Toggle between mocha and latte'
        'status:Show current theme'
        'transparency:Change transparency without changing theme'
    )
    
    local -a themes
    themes=(
        'mocha:Catppuccin Mocha (dark)'
        'latte:Catppuccin Latte (light)'
        'frappe:Catppuccin Frappe (dark)'
        'macchiato:Catppuccin Macchiato (dark)'
        'dynamic:Material You colors from wallpaper'
    )
    
    local -a transparency_values
    transparency_values=(
        '0:No transparency (opaque)'
        '50:50% transparency'
        '75:75% transparency'
        '85:85% transparency (recommended)'
        '90:90% transparency'
        '95:95% transparency'
        '100:Fully opaque'
    )
    
    if (( CURRENT == 2 )); then
        # Completing command
        _describe 'theme command' commands
    elif (( CURRENT == 3 )); then
        case $words[2] in
            set)
                # Completing theme name
                _describe 'theme name' themes
                ;;
            transparency)
                # Completing transparency value
                _describe 'transparency percentage' transparency_values
                ;;
        esac
    elif (( CURRENT == 4 )); then
        case $words[2] in
            set)
                # Completing -t flag or transparency value
                if [[ $words[3] != -* ]]; then
                    _arguments \
                        '-t[Transparency percentage (0-100)]:transparency:_transparency_values'
                fi
                ;;
        esac
    elif (( CURRENT == 5 )); then
        case $words[2] in
            set)
                # Completing transparency value after -t flag
                if [[ $words[4] == "-t" ]]; then
                    _describe 'transparency percentage' transparency_values
                fi
                ;;
        esac
    fi
}

_transparency_values() {
    local -a values
    values=(
        '0:No transparency'
        '50:50% transparent'
        '75:75% transparent'
        '85:85% transparent'
        '90:90% transparent'
        '95:95% transparent'
        '100:Fully opaque'
    )
    _describe 'transparency' values
}

# ============================================================================
# Wallpaper Command Completions
# ============================================================================

_wallpaper() {
    local -a commands
    commands=(
        'set:Set wallpaper from file path'
        'status:Show current wallpaper'
        'random:Set random wallpaper from theme folder'
    )
    
    if (( CURRENT == 2 )); then
        # Completing command
        _describe 'wallpaper command' commands
    elif (( CURRENT == 3 )); then
        case $words[2] in
            set)
                # Completing file path
                _files -g '*.{jpg,jpeg,png,heic}'
                ;;
        esac
    fi
}

# ============================================================================
# Register Completions
# ============================================================================

compdef _theme theme
compdef _wallpaper wallpaper
