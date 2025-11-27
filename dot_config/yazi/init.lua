-- ============================================================================
-- Yazi Plugin Initialization
-- ============================================================================
-- Documentation: https://yazi-rs.github.io/docs/plugins/overview
-- 
-- This file is run when yazi starts, allowing you to set up plugins
-- and customize behavior with Lua.
-- ============================================================================

-- ============================================================================
-- Plugin Setup
-- ============================================================================

-- Git integration (shows git status in file list)
-- Install: ya pkg add yazi-rs/plugins:git
-- require("git"):setup()

-- Full border UI (fancy borders around panes)
-- Install: ya pkg add yazi-rs/plugins:full-border
-- require("full-border"):setup()

-- ============================================================================
-- Custom Linemode: Size + Modified Time
-- ============================================================================
-- Shows both file size and modification time in the linemode
-- Usage: Set linemode = "size_and_mtime" in yazi.toml or use ;lc keybinding

function Linemode:size_and_mtime()
    local time = math.floor(self._file.cha.mtime or 0)
    if time == 0 then
        time = ""
    elseif os.date("%Y", time) == os.date("%Y") then
        time = os.date("%b %d %H:%M", time)
    else
        time = os.date("%b %d  %Y", time)
    end

    local size = self._file:size()
    return string.format("%s %s", size and ya.readable_size(size) or "-", time)
end

-- ============================================================================
-- Status Line Customization
-- ============================================================================
-- Uncomment to customize the status line appearance

-- function Status:name()
--     local h = self._tab.current.hovered
--     if not h then
--         return ""
--     end
--     return " " .. h.name
-- end

-- ============================================================================
-- Header Customization
-- ============================================================================
-- Uncomment to customize the header appearance

-- function Header:cwd()
--     local cwd = self._tab.current.cwd
--     local home = os.getenv("HOME") or ""
--     local path = tostring(cwd)
--     
--     if path:find(home, 1, true) == 1 then
--         path = "~" .. path:sub(#home + 1)
--     end
--     
--     return ui.Span(path):fg("cyan")
-- end

-- ============================================================================
-- Plugin Installation Notes
-- ============================================================================
--
-- Essential plugins (install with ya pkg add):
--
--   ya pkg add yazi-rs/plugins:git         # Git status in file list
--   ya pkg add yazi-rs/plugins:smart-enter # Enter directories or open files
--   ya pkg add yazi-rs/plugins:full-border # Fancy borders
--   ya pkg add yazi-rs/plugins:toggle-pane # Toggle preview/parent panes
--   ya pkg add yazi-rs/plugins:chmod       # Change file permissions
--
-- Optional plugins:
--
--   ya pkg add Reledia/glow                # Markdown preview with glow
--   ya pkg add dedukun/bookmarks           # Vi-like marks for directories
--   ya pkg add Rolv-Apneseth/starship      # Starship prompt integration
--
-- List installed plugins:
--   ya pkg list
--
-- Upgrade all plugins:
--   ya pkg upgrade
--
-- ============================================================================
