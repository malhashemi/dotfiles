#!/usr/bin/env zsh
# ZSH completion extension for extern-related just commands
#
# This extends (not replaces) the existing just completion to add
# custom repo name completion for extern-remove and extern-delete commands.
#
# Installation:
#   Add to your ~/.zshrc:
#     source /path/to/dubstack/.extern/scripts/completions.zsh

# Custom completion for extern repo names
_extern_repos() {
    local -a repos
    local catalog_script="$PWD/.extern/scripts/manage_catalog.py"
    
    if [[ -f "$catalog_script" ]]; then
        # Get repository names from the catalog
        repos=(${(f)"$(uv run "$catalog_script" completions 2>/dev/null)"})
        if [[ ${#repos[@]} -gt 0 ]]; then
            _describe 'external repository' repos
        fi
    fi
}

# Load the original just completion function if it exists
# This triggers autoload if _just hasn't been loaded yet
_just 2>/dev/null || true

# Only proceed if _just completion exists
if (( $+functions[_just] )); then
    # Save the original function
    functions[_just-original]=$functions[_just]
    
    # Redefine _just to add our custom logic while preserving everything else
    _just() {
        # Check if we're completing arguments for extern-remove or extern-delete
        if [[ $CURRENT -eq 3 ]]; then
            case $words[2] in
                extern-remove|extern-delete)
                    # Use our custom repo completion for these commands
                    _extern_repos
                    return 0
                    ;;
            esac
        fi
        
        # For everything else, delegate to the original just completion
        # This preserves all descriptions, formatting, and functionality
        _just-original "$@"
    }
    
    # Note: NO compdef needed - the function binding already exists,
    # we're just modifying the function definition
fi
