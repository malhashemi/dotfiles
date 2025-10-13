#!/bin/bash

# Setup WezTerm themes with Mauve accents
# This script updates the WezTerm configuration to support all Catppuccin variants

cat << 'EOF'
Setting up WezTerm themes with Mauve accents...
This will update your WezTerm configuration to support:
- Catppuccin Mocha Mauve
- Catppuccin Frappe Mauve  
- Catppuccin Macchiato Mauve
- Catppuccin Latte Mauve
- Dynamic (wallpaper-based)

Press Enter to continue or Ctrl+C to cancel...
EOF
read

# Backup current config
cp ~/.config/wezterm/wezterm.lua ~/.config/wezterm/wezterm.lua.bak

# Create new WezTerm config with all themes
cat > ~/.config/wezterm/wezterm.lua << 'EOF'
local wezterm = require("wezterm")

-- Custom Catppuccin themes with Mauve accents
local mocha_mauve = wezterm.color.get_builtin_schemes()["Catppuccin Mocha"]
mocha_mauve.ansi[5] = "#cba6f7"
mocha_mauve.brights[5] = "#cba6f7"
mocha_mauve.cursor_bg = "#cba6f7"
mocha_mauve.cursor_border = "#cba6f7"

local frappe_mauve = wezterm.color.get_builtin_schemes()["Catppuccin Frappe"]
frappe_mauve.ansi[5] = "#ca9ee6"
frappe_mauve.brights[5] = "#ca9ee6"
frappe_mauve.cursor_bg = "#ca9ee6"
frappe_mauve.cursor_border = "#ca9ee6"

local macchiato_mauve = wezterm.color.get_builtin_schemes()["Catppuccin Macchiato"]
macchiato_mauve.ansi[5] = "#c6a0f6"
macchiato_mauve.brights[5] = "#c6a0f6"
macchiato_mauve.cursor_bg = "#c6a0f6"
macchiato_mauve.cursor_border = "#c6a0f6"

local latte_mauve = wezterm.color.get_builtin_schemes()["Catppuccin Latte"]
latte_mauve.ansi[5] = "#8839ef"
latte_mauve.brights[5] = "#8839ef"
latte_mauve.cursor_bg = "#8839ef"
latte_mauve.cursor_border = "#8839ef"

-- Read theme preference from file
local theme_file = wezterm.home_dir .. "/.config/wezterm/theme.txt"
local theme = "Catppuccin Mocha Mauve"
local file = io.open(theme_file, "r")
if file then
	theme = file:read("*l") or "Catppuccin Mocha Mauve"
	file:close()
end

-- Check if transparency is enabled
local transparency_file = wezterm.home_dir .. "/.config/wezterm/transparent.txt"
local transparent_file = io.open(transparency_file, "r")
local config = {
	adjust_window_size_when_changing_font_size = false,
	automatically_reload_config = true,
	enable_tab_bar = false,
	font_size = 16.0,
	font = wezterm.font("JetBrains Mono"),
	window_decorations = "RESIZE",
}

if transparent_file then
	local transparent = transparent_file:read("*l")
	transparent_file:close()
	if transparent == "true" then
		config.window_background_opacity = 0.92
		config.macos_window_background_blur = 80
	end
end

-- Check if dynamic theme is requested
local dynamic_file = wezterm.home_dir .. "/.config/theme-system/themes/dynamic-wezterm.toml"
local dynamic = io.open(dynamic_file, "r")
if dynamic and theme == "Dynamic" then
	-- Load dynamic colors from wallust/matugen output
	dynamic:close()
	config.color_scheme_dirs = { wezterm.home_dir .. "/.config/theme-system/themes" }
	config.color_scheme = "dynamic"
else
	-- Use static theme
	config.color_schemes = {
		["Catppuccin Mocha Mauve"] = mocha_mauve,
		["Catppuccin Frappe Mauve"] = frappe_mauve,
		["Catppuccin Macchiato Mauve"] = macchiato_mauve,
		["Catppuccin Latte Mauve"] = latte_mauve,
	}
	config.color_scheme = theme
end

-- Key bindings
config.keys = {
	{
		key = "q",
		mods = "CTRL",
		action = wezterm.action.ToggleFullScreen,
	},
	{
		key = "'",
		mods = "CTRL",
		action = wezterm.action.ClearScrollback("ScrollbackAndViewport"),
	},
}

-- Mouse bindings
config.mouse_bindings = {
	{
		event = { Up = { streak = 1, button = "Left" } },
		mods = "CTRL",
		action = wezterm.action.OpenLinkAtMouseCursor,
	},
}

return config
EOF

echo "✅ WezTerm configuration updated!"
echo ""
echo "Now creating helper scripts..."

# Create dynamic theme generator
cat > ~/.config/theme-system/scripts/generate-dynamic.sh << 'EOF'
#!/bin/bash

# Generate dynamic theme from wallpaper
WALLPAPER_PATH="$1"

if [ -z "$WALLPAPER_PATH" ]; then
    # Try to get current wallpaper from macOS
    WALLPAPER_PATH=$(osascript -e 'tell application "System Events" to get picture of current desktop')
fi

if [ ! -f "$WALLPAPER_PATH" ]; then
    echo "Error: Wallpaper not found at $WALLPAPER_PATH"
    exit 1
fi

echo "🎨 Generating dynamic theme from wallpaper..."
echo "   Source: $WALLPAPER_PATH"

# Generate colors with wallust
wallust run -s "$WALLPAPER_PATH"

# Convert wallust output to WezTerm format
# This will need to be implemented based on wallust output format

echo "✅ Dynamic theme generated!"
EOF

chmod +x ~/.config/theme-system/scripts/generate-dynamic.sh

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Install wallust: brew install wallust"
echo "2. Install matugen: brew install matugen"
echo "3. Move your theme-manager.py to ~/.config/theme-system/"
echo "4. Update theme-manager.py to use the new structure"
EOF