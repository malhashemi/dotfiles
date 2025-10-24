-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua

-- ============================================================================
-- THEME SYSTEM INTEGRATION
-- ============================================================================
-- The theme system uses three autocmd-based modules for automatic behavior:
--
-- 1. theme-persistence.lua
--    - Saves current colorscheme on every ColorScheme event
--    - Loads saved colorscheme on startup
--    - Works with ANY colorscheme (not just Catppuccin/dynamic)
--
-- 2. theme-filewatcher.lua  
--    - Watches generated files (colors-nvim.lua, theme-state.lua, opacity-data.lua)
--    - Auto-reloads when external theme changes detected (theme set/mode/opacity)
--    - Triggers on FocusGained and BufEnter events (~2 second detection)
--
-- 3. opacity-manager.lua
--    - Applies opacity settings after every ColorScheme event
--    - Handles both Neovide (vim.g variables) and terminal (transparency)
--    - Ensures consistent opacity across theme switches
--
-- External theme changes (via `theme` CLI) are automatically detected and applied.
-- Manual theme changes (via keybindings or :colorscheme) are automatically persisted.
-- ============================================================================

-- Theme Persistence - Automatically save and load theme preference
require('config.theme-persistence').setup()

-- Theme File Watcher - Automatically reload when external changes detected
require('config.theme-filewatcher').setup()

-- Opacity Manager - Apply opacity after every colorscheme change
require('config.opacity-manager').setup()
